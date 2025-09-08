import json
from fastapi import FastAPI, HTTPException,Path,Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field,computed_field
from typing import Annotated, Literal,Optional

app = FastAPI()

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="The ID of the patient", example="P001")]
    name: Annotated[str, Field(..., description="The name of the patient", example="John Doe")]
    city: Annotated[str, Field(..., description="The city where the patient resides", example="New York")]
    age: Annotated[int, Field(..., description="The age of the patient", example=30)]
    height: Annotated[float, Field(..., description="The height of the patient in meters", example=1.75)]
    gender: Annotated[Literal["Male", "Female", "Other"], Field(..., description="The gender of the patient", example="Male")]
    weight: Annotated[float, Field(..., description="The weight of the patient in kilograms", example=70)]

    @computed_field
    @property
    def bmi(self) -> Optional[float]:   
        if self.weight and self.height:
            return self.weight / (self.height ** 2)
        return None

    @computed_field
    @property
    def bmi_category(self) -> str:      
        bmi = self.bmi
        if bmi is None:
            return "Unknown"
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 24.9:
            return "Normal weight"
        elif 25 <= bmi < 29.9:
            return "Overweight"
        else:
            return "Obesity"

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(description="The name of the patient", example="John Doe")]
    city: Annotated[Optional[str], Field(description="The city where the patient resides", example="New York")]
    age: Annotated[Optional[int], Field(description="The age of the patient", example=30)]
    height: Annotated[Optional[float], Field(description="The height of the patient in meters", example=1.75)]
    gender: Annotated[Optional[Literal["Male", "Female", "Other"]], Field(description="The gender of the patient", example="Male")]
    weight: Annotated[Optional[float], Field(description="The weight of the patient in kilograms", example=70)]

def get_patient_data():
    with open("patients.JSON") as f:
        data = json.load(f)
    return data

def save_patient_data(data):
    with open("patients.JSON", "w") as f:
        json.dump(data, f)

@app.get("/")
def read_root():
    return {"Message": "Patients Management System API"}
@app.get("/about")
def read_about():
    return {"Message": "A fully functional API for managing patient data."}
@app.get("/view")
def read_view():
    data = get_patient_data()
    return data
@app.get("/patient/{patient_id}")
def view_patient(patient_id: str = Path(..., description="The ID of the patient to retrieve",example="P001")):
    data = get_patient_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")
@app.get('/sort')
def sort_patients(sort_by:str = Query(..., description="sort on the basis of height weight and BMI"),order:str = Query('asc',description='sort in basis of ascending or descending order')):
    valid_fields = ['height', 'weight', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Must be one of {valid_fields}")

    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order. Must be 'asc' or 'desc'")
    data = get_patient_data()
    sort_order = True if order == 'desc' else False
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by), reverse=sort_order)
    return sorted_data
@app.post('/create')
def create_patiet(patient:Patient):
    #loading existing data
    data = get_patient_data()  
    #checking if patient id already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient ID already exists")    
    #if new patient id then adding the patient to the data
    data[patient.id] = patient.model_dump(exclude=['id'])
    #save it in the jsnon file
    save_patient_data(data)
    return JSONResponse(content={"Message": "Patient created successfully"}, status_code=201)
@app.put('/update/{patient_id}')
def update_patient(patient_id: str = Path(..., description="The ID of the patient to update",example="P001"), patient_update: PatientUpdate = ...):
    data = get_patient_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    existing_patient = data[patient_id]
    updated_data =  patient_update.model_dump(exclude_unset=True)
# Update only the fields that are provided in the request
    for key, value in updated_data.items():
        existing_patient[key] = value
#existing_patient -> pydantic object -> updated bmi + verdict
    existing_patient['id'] = patient_id

    Patient_pydantic_obj = Patient(**existing_patient)

# -> pydantic object -> dict
    existing_patient = Patient_pydantic_obj.model_dump(exclude={'id'})

    data[patient_id] = existing_patient

    save_patient_data(data)
    return JSONResponse(content={"Message": "Patient updated successfully"})
@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str = Path(..., description="The ID of the patient to delete",example="P001")):
    data = get_patient_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    del data[patient_id]
    save_patient_data(data)
    return JSONResponse(content={"Message": "Patient deleted successfully"})