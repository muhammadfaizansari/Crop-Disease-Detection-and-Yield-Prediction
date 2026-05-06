from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import numpy as np
import json
import uuid
import tensorflow as tf
import pickle
import pandas as pd

app = Flask(__name__)

# ==============================
# LOAD MODELS
# ==============================

# Disease detection model
model = tf.keras.models.load_model("models/crop_disease_detection_model.keras", compile=False)

# Yield prediction model
yield_model = pickle.load(open('models/dtr.pkl', 'rb'))
yield_preprocessor = pickle.load(open('models/preprocessor.pkl', 'rb'))
yield_df = pd.read_csv('yield_df.csv')

area_options = sorted(yield_df['Area'].dropna().astype(str).unique().tolist())
item_options = sorted(yield_df['Item'].dropna().astype(str).unique().tolist())

# ==============================
# LOAD CLASS MAPPING (CRITICAL)
# ==============================

with open("models/class_names.json", "r") as f:
    class_names = json.load(f)

with open("plant_disease.json", "r") as file:
    disease_info = json.load(file)

# Validate mapping
if len(class_names) != len(disease_info):
    raise ValueError("Mismatch between model classes and disease info JSON")

# ==============================
# IMAGE PREPROCESSING
# ==============================

def extract_features(image_path):
    image = tf.keras.utils.load_img(image_path, target_size=(160, 160))
    img_array = tf.keras.utils.img_to_array(image)
    img_array = np.expand_dims(img_array, axis=0)

    # ✅ Correct preprocessing (EfficientNet)
    img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)

    return img_array

# ==============================
# DISEASE PREDICTION
# ==============================

def model_predict(image_path):
    img_array = extract_features(image_path)

    predictions = model.predict(img_array, verbose=0)[0]

    # Debug (optional)
    print("Predictions:", predictions)
    print("Sum:", np.sum(predictions))

    best_index = int(np.argmax(predictions))
    best_class_name = class_names[best_index]
    best_confidence = round(float(predictions[best_index] * 100), 2)

    # Map to disease info
    best_disease = next(
        (d for d in disease_info if d["name"] == best_class_name),
        {"name": best_class_name, "cause": "Unknown", "cure": "Unknown"}
    )

    return best_disease, best_confidence

# ==============================
# ROUTES
# ==============================

@app.route('/uploadimages/<path:filename>')
def uploaded_images(filename):
    return send_from_directory('./uploadimages', filename)

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html', area_options=area_options, item_options=item_options)

# ==============================
# YIELD PREDICTION
# ==============================

@app.route('/predict', methods=['GET', 'POST'])
def predict_yield():
    if request.method == 'POST':
        try:
            year = int(request.form.get('Year'))
            rainfall = float(request.form.get('average_rain_fall_mm_per_year'))
            pesticides = float(request.form.get('pesticides_tonnes'))
            temperature = float(request.form.get('avg_temp'))
            area = request.form.get('Area')
            crop_item = request.form.get('Item')

            features = pd.DataFrame([{
                "Area": area,
                "Item": crop_item,
                "Year": year,
                "average_rain_fall_mm_per_year": rainfall,
                "pesticides_tonnes": pesticides,
                "avg_temp": temperature
            }])

            transformed = yield_preprocessor.transform(features)
            prediction = yield_model.predict(transformed)
            predicted_yield = round(float(prediction[0]), 2)

            return render_template(
                'home.html',
                yield_prediction=predicted_yield,
                yield_submitted=True,
                area_options=area_options,
                item_options=item_options
            )

        except Exception as e:
            return render_template(
                'home.html',
                yield_error=str(e),
                yield_submitted=True,
                area_options=area_options,
                item_options=item_options
            )

    return redirect(url_for('home'))

# ==============================
# IMAGE UPLOAD + PREDICTION
# ==============================

@app.route('/upload/', methods=['POST', 'GET'])
def uploadimage():
    if request.method == "POST":
        image = request.files['image']

        temp_name = f"uploadimages/temp_{uuid.uuid4().hex}_{image.filename}"
        image.save(temp_name)

        prediction, confidence = model_predict(temp_name)

        return render_template(
            'home.html',
            result=True,
            imagepath=temp_name,
            prediction=prediction,
            primary_confidence=confidence,
            area_options=area_options,
            item_options=item_options
        )

    return redirect('/')

# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":
    app.run(debug=True)