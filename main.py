from flask import Flask, render_template, request
import pickle
import os
import pandas as pd

app = Flask(__name__)



# Plan pricing
plan_prices = {
    "Basic Plan": 8000,
    "Standard Plan": 20000,
    "Comprehensive Plan": 25000,
    "Executive Plan": 35000
}

def calculate_risk_score(age, diabetes, blood_pressure, any_transplants, any_chronic_diseases, height, weight,
                         known_allergies, history_of_cancer, num_major_surgeries, sex, children, smoker, region, bmis):
    score = 0
    score += min(age, 100) * 0.2
    score += 10 if diabetes else 0
    score += 10 if blood_pressure else 0
    score += 15 if any_transplants else 0
    score += 10 if any_chronic_diseases else 0
    score += 5 if known_allergies else 0
    score += 10 if history_of_cancer else 0

    if bmis < 18.5 or bmis >= 30:
        score += 10
    elif 25 <= bmis < 30:
        score += 5

    score += 20 if smoker else 0
    score += num_major_surgeries * 2
    #score =min(age,100)×0.2+(10×diabetes)+(10×blood_pressure)+(15×any_transplants)+(10×any_chronic_diseases)+(5×known_allergies)+(10×history_of_cancer)+(20×smoker)+(2×num_major_surgeries)


    return min(score, 100)

def prediction_model(risk_score, region):
    import joblib

    model = joblib.load("health_premium_model.pkl")
    test_data = pd.DataFrame([{
        "RiskScore": risk_score,
        "region": region
    }])
    return model.predict(test_data)[0]

def plan_recommendation(selected_plan, predicted_premium):
    base_price = plan_prices[selected_plan]
    if predicted_premium > base_price:
        extra_risk = predicted_premium - base_price
        return {
            "Status": "Undercovered",
            "SuggestedUpgrade": True,
            "ExtraToPay": round(extra_risk, 2),
            "Message": f"Your predicted premium is ₹{predicted_premium}, which is ₹{extra_risk} higher than {selected_plan}. Consider upgrading."
        }
    return None

def smart_discount_engine(selected_plan, predicted_premium):
    base_price = plan_prices[selected_plan]
    max_discount_rate = {
        "Basic Plan": 0.10,
        "Standard Plan": 0.15,
        "Comprehensive Plan": 0.20,
        "Executive Plan": 0.25
    }

    allowed_discount = base_price * max_discount_rate[selected_plan]
    suggested_price = max(predicted_premium, base_price - allowed_discount)

    if predicted_premium < base_price:
        return {
            "Action": "Eligible for Limited Discount",
            "SuggestedPremium": round(suggested_price, 2),
            "Message": f"Predicted premium is ₹{predicted_premium}. You may offer max ₹{round(allowed_discount, 2)} discount on {selected_plan}."
        }
    return None
@app.route('/', methods=['GET'])
def home():
    return render_template('insurance_form.html')


@app.route('/predict', methods=['GET', 'POST'],endpoint='predict_premium')
def predict():
    if request.method == 'POST':
        # Extracting form values
        age = int(request.form['Age'])
        diabetes = request.form['Diabetes'] == 'True'
        blood_pressure = request.form['BloodPressureProblems'] == 'True'
        any_transplants = request.form['AnyTransplants'] == 'True'
        any_chronic_diseases = request.form['AnyChronicDiseases'] == 'True'
        height = float(request.form['Height'])
        weight = float(request.form['Weight'])
        known_allergies = request.form['KnownAllergies']
        history_of_cancer = request.form['HistoryOfCancerInFamily'] == 'True'
        num_major_surgeries = int(request.form['NumberOfMajorSurgeries'])
        sex = request.form['sex']
        children = int(request.form['children'])
        smoker = request.form['smoker'] == 'True'
        region = request.form['region']
        bmis = float(request.form['bmis'])
        plan = request.form['selected_plan']

        # Predict
        risk_score = calculate_risk_score(
            age, diabetes, blood_pressure, any_transplants, any_chronic_diseases,
            height, weight, known_allergies, history_of_cancer, num_major_surgeries,
            sex, children, smoker, region, bmis
        )

        predictor = prediction_model(risk_score, region)
        recommendation = plan_recommendation(plan, predictor)
        discount = smart_discount_engine(plan, predictor)

        return render_template('result.html',
                               predicted_premium=round(predictor, 2),
                               recommendation=recommendation,
                               discount=discount,
                               selected_plan=plan)

    return render_template('insurance_form.html')

if __name__ == '__main__':
    app.run(debug=True)
