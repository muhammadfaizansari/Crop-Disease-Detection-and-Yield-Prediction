from flask import Flask, render_template,request,redirect,send_from_directory,url_for
import numpy as np
import json
import uuid
import tensorflow as tf
import pickle
import pandas as pd

app = Flask(__name__)
model = tf.keras.models.load_model("models/crop_disease_detection_model.keras", compile=False)

# Load yield prediction models
yield_model = pickle.load(open('models/dtr.pkl', 'rb'))
yield_preprocessor = pickle.load(open('models/preprocessor.pkl', 'rb'))
yield_df = pd.read_csv('yield_df.csv')

area_options = sorted(yield_df['Area'].dropna().astype(str).unique().tolist())
item_options = sorted(yield_df['Item'].dropna().astype(str).unique().tolist())
label = ['Apple___Apple_scab',
 'Apple___Black_rot',
 'Apple___Cedar_apple_rust',
 'Apple___healthy',
 'Background_without_leaves',
 'Blueberry___healthy',
 'Cherry___Powdery_mildew',
 'Cherry___healthy',
 'Corn___Cercospora_leaf_spot Gray_leaf_spot',
 'Corn___Common_rust',
 'Corn___Northern_Leaf_Blight',
 'Corn___healthy',
 'Grape___Black_rot',
 'Grape___Esca_(Black_Measles)',
 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
 'Grape___healthy',
 'Orange___Haunglongbing_(Citrus_greening)',
 'Peach___Bacterial_spot',
 'Peach___healthy',
 'Pepper,_bell___Bacterial_spot',
 'Pepper,_bell___healthy',
 'Potato___Early_blight',
 'Potato___Late_blight',
 'Potato___healthy',
 'Raspberry___healthy',
 'Soybean___healthy',
 'Squash___Powdery_mildew',
 'Strawberry___Leaf_scorch',
 'Strawberry___healthy',
 'Tomato___Bacterial_spot',
 'Tomato___Early_blight',
 'Tomato___Late_blight',
 'Tomato___Leaf_Mold',
 'Tomato___Septoria_leaf_spot',
 'Tomato___Spider_mites Two-spotted_spider_mite',
 'Tomato___Target_Spot',
 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
 'Tomato___Tomato_mosaic_virus',
 'Tomato___healthy']

# with open("plant_disease.json",'r') as file:
#     plant_disease = json.load(file)
with open("models/class_names.json", "r") as f:
    class_names = json.load(f)

with open("plant_disease.json", "r") as file:
    disease_info = json.load(file)

model_output_shape = model.output_shape[0] if isinstance(model.output_shape, list) else model.output_shape
model_output_units = int(model_output_shape[-1])
if model_output_units != len(disease_info):
    raise ValueError("Model output classes and class mapping are inconsistent")

# print(plant_disease[4])

@app.route('/uploadimages/<path:filename>')
def uploaded_images(filename):
    return send_from_directory('./uploadimages', filename)

@app.route('/',methods = ['GET'])
def home():
    return render_template('home.html', area_options=area_options, item_options=item_options)

@app.route('/predict', methods=['GET', 'POST'])
def predict_yield():
    if request.method == 'POST':
        selected_area = request.form.get('Area')
        selected_item = request.form.get('Item')
        year = request.form.get('Year')
        rainfall = request.form.get('average_rain_fall_mm_per_year')
        pesticides = request.form.get('pesticides_tonnes')
        temperature = request.form.get('avg_temp')

        try:
            # Extract form values
            year_num = int(year)
            rainfall_num = float(rainfall)
            pesticides_num = float(pesticides)
            temperature_num = float(temperature)

            # Create DataFrame with correct column names for preprocessing
            features = pd.DataFrame([{
                "Area": selected_area,
                "Item": selected_item,
                "Year": year_num,
                "average_rain_fall_mm_per_year": rainfall_num,
                "pesticides_tonnes": pesticides_num,
                "avg_temp": temperature_num
            }])

            # Apply preprocessing and prediction
            transformed = yield_preprocessor.transform(features)
            prediction = yield_model.predict(transformed)
            predicted_yield = round(float(prediction[0]), 2)

            return render_template(
                'home.html',
                yield_prediction=predicted_yield,
                yield_submitted=True,
                area_options=area_options,
                item_options=item_options,
                selected_area=selected_area,
                selected_item=selected_item,
                year=year,
                rainfall=rainfall,
                pesticides=pesticides,
                temperature=temperature
            )
        
        except Exception as e:
            return render_template(
                'home.html',
                yield_error=str(e),
                yield_submitted=True,
                area_options=area_options,
                item_options=item_options,
                selected_area=selected_area,
                selected_item=selected_item,
                year=year,
                rainfall=rainfall,
                pesticides=pesticides,
                temperature=temperature
            )
    
    else:
        # GET request - return clean state
        return redirect(url_for('home'))

def extract_features(image_path):
    image = tf.keras.utils.load_img(image_path, target_size=(160, 160))
    img_array = tf.keras.utils.img_to_array(image)
    # img_array = img_array / 255.0
    img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def model_predict(image):
    img_array = extract_features(image)
    predictions = model.predict(img_array, verbose=0)[0]

    print("Predictions:", predictions)
    print("Sum:", np.sum(predictions))

    # For single-label classification, use argmax to pick the single best class
    best_index = int(np.argmax(predictions))

    best_class_name = class_names[best_index]

    best_disease = next(
    (d for d in disease_info if d["name"] == best_class_name),
    {"name": best_class_name, "cause": "Unknown", "cure": "Unknown"}
    )

    best_confidence = round(float(predictions[best_index] * 100), 2)

    return best_disease, best_confidence

@app.route('/upload/',methods = ['POST','GET'])
def uploadimage():
    if request.method == "POST":
        image = request.files['img']
        temp_name = f"uploadimages/temp_{uuid.uuid4().hex}"
        image.save(f'{temp_name}_{image.filename}')
        print(f'{temp_name}_{image.filename}')
        prediction, primary_confidence = model_predict(f'./{temp_name}_{image.filename}')
        return render_template(
            'home.html',
            result=True,
            imagepath=f'/{temp_name}_{image.filename}',
            prediction=prediction,
            primary_confidence=primary_confidence,
            area_options=area_options,
            item_options=item_options
        )
    
    else:
        return redirect('/')
        
    
if __name__ == "__main__":
    app.run(debug=True)
