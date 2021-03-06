import tensorflow as tf
from tensorflow import keras
import numpy as np
import PIL
import json
import urllib.parse
import boto3

# predicter function
def predict_saved_model(img_path, model_path):
    '''
    Takes the saved model to make an inference on a given image
    '''
    # upload the saved and trained model
    model = tf.keras.models.load_model(model_path)
    image_size = (180, 180)
    img = keras.preprocessing.image.load_img(
        img_path, target_size=image_size
        )
    img_array = keras.preprocessing.image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # Create batch axis

    predictions = model.predict(img_array)
    score = predictions[0]
    print(f'This image {img_path} is {100*(1-score)} percent cat and {100*score} percent dog.')

    return {"cat": str((100 * (1 - score))[0]), "dog": str((100 * score)[0])}


# app handler
def handler(event, context):
    # Set up some variables we'll need
    print("Prediction in progress ...")
    image_path = "/tmp/image.jpg"
    model_path = "/tmp/model.h5"


    # Connect to AWS Services
    s3_client = session.resource('s3') #boto3.client('s3')

    ssm_client = session.resource('ssm') #boto3.client('ssm')


    # S3 Image object name
    s3_img = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8'
        )


    # S3 bucket name
    s3_bucket = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['bucket']['name'], encoding='utf-8'
        )


    # S3 Model object in bucket
    s3_model_path = ssm_client.get_parameters(
        Names=['model_path'], WithDecryption=True
        )["Parameters"][0]["Value"].replace("\n", "")


    # S3 Model bucket
    s3_model_bucket = ssm_client.get_parameters(
        Names=['model_bucket'], WithDecryption=True
        )["Parameters"][0]["Value"]


    # Download image container
    with open(image_path, 'wb') as f:
        s3_client.download_fileobj(s3_bucket, s3_img, f)


    # Download model container
    with open(model_path, 'wb') as f:
        s3_client.download_fileobj(s3_model_bucket, s3_model_path, f)


    # Make the inference
    prediction = predict_saved_model(image_path, model_path)

    return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
                },
            "body": json.dumps({
                "cat": prediction["cat"],
                "dog": prediction["dog"]
                })
            }
