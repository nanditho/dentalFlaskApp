import os
import random
import string
import pathlib
import cloudinary
import numpy as np
from PIL import Image
import tensorflow as tf
from GeneratePDF import GeneratePDF
from IPython.display import display
from cloudinary.uploader import upload
from tensorflow.python.framework.ops import disable_eager_execution
from my_custom_detector.models.research.object_detection.utils import label_map_util
from my_custom_detector.models.research.object_detection.utils import ops as utils_ops
from my_custom_detector.models.research.object_detection.utils import visualization_utils as vis_util

isDetectionCompleted = False
uploadedTestedImages = []


def TeethDetection(testImagesDir, resultImagesDir, cloudinaryUploadFolder, patientDetails):
    global isDetectionCompleted
    print('Image Detection Started!')
    disable_eager_execution()
    # patch tf1 into `utils.ops`
    utils_ops.tf = tf.compat.v1

    # Patch the location of gfile
    tf.gfile = tf.io.gfile

    def load_model():
        model_dir = "my_custom_detector/trained-inference-graphs/saved_model"
        model = tf.compat.v2.saved_model.load(model_dir, None)
        model = model.signatures['serving_default']

        return model

    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = 'my_custom_detector/training/object-detection.pbtxt'
    category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)

    # If you want to test the code with your images, just add path to the images to the TEST_IMAGE_PATHS.
    PATH_TO_TEST_IMAGES_DIR = pathlib.Path(os.getcwd() + testImagesDir)
    TEST_IMAGE_PATHS = sorted(list(PATH_TO_TEST_IMAGES_DIR.glob("*.jpg")))

    detection_model = load_model()

    def run_inference_for_single_image(model, image):
        image = np.asarray(image)
        # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
        input_tensor = tf.convert_to_tensor(image)
        # The model expects a batch of images, so add an axis with `tf.newaxis`.
        input_tensor = input_tensor[tf.newaxis, ...]

        # Run inference
        output_dict = model(input_tensor)

        # All outputs are batches tensors.
        # Convert to numpy arrays, and take index [0] to remove the batch dimension.
        # We're only interested in the first num_detections.
        with tf.compat.v1.Session():
            print(output_dict['num_detections'].eval())  # debugging line
            num_detections = int(output_dict.pop('num_detections').eval()[0])

            output_dict = {key: value[0, :num_detections].eval()  # changed numpy to eval
                           for key, value in output_dict.items()}
            output_dict['num_detections'] = num_detections

            # detection_classes should be ints.
            output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)

        # Handle models with masks:
        if 'detection_masks' in output_dict:
            # Reframe the bbox mask to the image size.
            detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                output_dict['detection_masks'], output_dict['detection_boxes'],
                image.shape[0], image.shape[1])
            detection_masks_reframed = tf.cast(detection_masks_reframed > 0.5,
                                               tf.uint8)
            output_dict['detection_masks_reframed'] = detection_masks_reframed.numpy()

        return output_dict

    def show_inference(model, imagePath):
        # the array based representation of the image will be used later in order to prepare the
        # result image with boxes and labels on it.
        image_np = np.array(Image.open(imagePath))
        # Actual detection.
        output_dict = run_inference_for_single_image(model, image_np)
        # Visualization of the results of a detection.
        vis_util.visualize_boxes_and_labels_on_image_array(
            image_np,
            output_dict['detection_boxes'],
            output_dict['detection_classes'],
            output_dict['detection_scores'],
            category_index,
            instance_masks=output_dict.get('detection_masks_reframed', None),
            use_normalized_coordinates=True,
            line_thickness=4)
        outputImage = Image.fromarray(image_np)
        randomImageName = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
        outputImage.save(os.getcwd() + resultImagesDir + "\\" + randomImageName + '.jpg')
        global isDetectionCompleted
        isDetectionCompleted = True
        '''
        display image in python using code below
        image_out = Image.new(mode="RGB", size=outputImage.size)
        tuples = [tuple(x) for x in outputImage.getdata()]
        image_out.putdata(tuples)
        image_out.show()
        
        display image in python in jupyter notebook using code below
        display(outputImage)
        '''

    def get_jpg_files(directory):
        jpg_files = []
        for file in os.listdir(directory):
            if file.endswith(".jpg") or file.endswith(".JPG"):
                jpg_files.append(os.path.join(directory, file))
        return jpg_files

    for image_path in TEST_IMAGE_PATHS:
        show_inference(detection_model, image_path)

    if isDetectionCompleted:
        # Config Cloudinary
        cloudinary.config(
            cloud_name="dg5esqkeb",
            api_key="654286619656251",
            api_secret="7-JkBR5t_EU8lN3ArIdvsZ1txCw",
            secure=True
        )
        # Upload Detected Images in Cloudinary
        directory_path = os.getcwd() + resultImagesDir
        jpg_files = get_jpg_files(directory_path)
        folderName = str(cloudinaryUploadFolder).replace("PatientUploaded", "PatientResults")
        global uploadedTestedImages
        for image in jpg_files:
            randomImageName = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
            result = upload(file=image, public_id=randomImageName, tags="PatientImages", folder=folderName)
            uploadedTestedImages.append(result['secure_url'])

        GeneratePDF(patientDetails, uploadedTestedImages, cloudinaryUploadFolder)
        print('Image detection completed.....')
    else:
        print('No Image detection performed.....')
