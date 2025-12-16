from utils import inference_with_api

prompt = 'Locate the black fan in the image. Report bbox coordinates in JSON format.'
img_url = "./sim.png"
model_response = inference_with_api(img_url, prompt)
print(model_response)