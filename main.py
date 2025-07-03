# main.py (Backend FastAPI)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
import datetime

# Inicializa la aplicación FastAPI
app = FastAPI(
    title="API de Organizador de Citas",
    description="Una API para gestionar citas de un negocio, con configuración de horario y duración de citas.",
    version="1.0.0",
)

# Configuración de CORS
# Permite que el frontend (que se ejecutará en un navegador) se comunique con este backend.
# En un entorno de producción, deberías restringir 'origins' a la URL específica de tu frontend.
origins = [
    "http://localhost",
    "http://localhost:8000", # Por si el frontend se sirve desde otro puerto
    "null" # Para permitir el acceso desde archivos HTML locales (file://)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Permite todos los encabezados
)

# --- Modelos de Pydantic para validación de datos ---

class BusinessConfig(BaseModel):
    """Modelo para la configuración del horario del negocio."""
    business_start_time: str = Field(..., example="09:00", description="Hora de inicio de la jornada laboral (HH:MM).")
    business_end_time: str = Field(..., example="17:00", description="Hora de fin de la jornada laboral (HH:MM).")
    appointment_duration: int = Field(..., gt=0, description="Duración estándar de una cita en minutos.")

class AppointmentCreate(BaseModel):
    """Modelo para crear una nueva cita."""
    date: str = Field(..., example="2025-07-04", description="Fecha de la cita (YYYY-MM-DD).")
    time: str = Field(..., example="10:30", description="Hora de inicio de la cita (HH:MM).")
    client_name: str = Field(..., min_length=1, description="Nombre del cliente.")
    duration: Optional[int] = Field(None, gt=0, description="Duración de esta cita específica en minutos. Si no se proporciona, se usará la duración por defecto del negocio.")

class Appointment(AppointmentCreate):
    """Modelo para una cita existente, incluyendo su ID."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único de la cita.")

# --- Almacenamiento de datos en memoria (para este ejemplo) ---
# En una aplicación real, esto se reemplazaría por una base de datos (MongoDB, PostgreSQL, etc.)
appointments_db: List[Appointment] = []
business_config_db: BusinessConfig = BusinessConfig(
    business_start_time="09:00",
    business_end_time="17:00",
    appointment_duration=30
)

# --- Funciones de utilidad ---

def time_to_minutes(time_str: str) -> int:
    """Convierte una cadena de tiempo (HH:MM) a minutos desde la medianoche."""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def minutes_to_time(total_minutes: int) -> str:
    """Convierte minutos desde la medianoche a una cadena de tiempo (HH:MM)."""
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h:02d}:{m:02d}"

def is_overlap(
    new_start_minutes: int, new_end_minutes: int,
    existing_start_minutes: int, existing_end_minutes: int
) -> bool:
    """Verifica si dos rangos de tiempo se solapan."""
    return (new_start_minutes < existing_end_minutes and new_end_minutes > existing_start_minutes)

# --- Endpoints de la API ---

@app.get("/config", response_model=BusinessConfig, summary="Obtener configuración del negocio")
async def get_business_config():
    """
    Obtiene la configuración actual del horario y duración de citas del negocio.
    """
    return business_config_db

@app.put("/config", response_model=BusinessConfig, summary="Actualizar configuración del negocio")
async def update_business_config(config: BusinessConfig):
    """
    Actualiza la configuración del horario y duración de citas del negocio.
    """
    global business_config_db
    business_config_db = config
    return business_config_db

@app.get("/appointments", response_model=List[Appointment], summary="Obtener todas las citas o filtrar por fecha")
async def get_appointments(date: Optional[str] = None):
    """
    Obtiene una lista de todas las citas agendadas.
    Opcionalmente, puedes filtrar las citas por una fecha específica (YYYY-MM-DD).
    """
    if date:
        # Validar formato de fecha
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD.")
        return [appt for appt in appointments_db if appt.date == date]
    return sorted(appointments_db, key=lambda x: (x.date, x.time))

@app.post("/appointments", response_model=Appointment, status_code=201, summary="Agendar una nueva cita")
async def create_appointment(appointment: AppointmentCreate):
    """
    Agenda una nueva cita.
    Verifica la disponibilidad y el horario del negocio antes de agendar.
    """
    # Usar la duración por defecto si no se proporciona una específica para la cita
    appt_duration = appointment.duration if appointment.duration is not None else business_config_db.appointment_duration

    appt_start_minutes = time_to_minutes(appointment.time)
    appt_end_minutes = appt_start_minutes + appt_duration

    business_start_minutes = time_to_minutes(business_config_db.business_start_time)
    business_end_minutes = time_to_minutes(business_config_db.business_end_time)

    # Validar que la cita esté dentro del horario de negocio
    if appt_start_minutes < business_start_minutes or appt_end_minutes > business_end_minutes:
        raise HTTPException(status_code=400, detail="La hora de la cita está fuera del horario de negocio.")

    # Validar solapamiento de citas para la misma fecha
    for existing_appt in appointments_db:
        if existing_appt.date == appointment.date:
            existing_appt_actual_duration = existing_appt.duration if existing_appt.duration is not None else business_config_db.appointment_duration
            existing_start_minutes = time_to_minutes(existing_appt.time)
            existing_end_minutes = existing_start_minutes + existing_appt_actual_duration

            if is_overlap(appt_start_minutes, appt_end_minutes, existing_start_minutes, existing_end_minutes):
                raise HTTPException(status_code=409, detail="Ya existe una cita agendada que se solapa con este horario.")

    # Crear la nueva cita con un ID único y la duración real utilizada
    new_appointment = Appointment(
        id=str(uuid.uuid4()),
        date=appointment.date,
        time=appointment.time,
        client_name=appointment.client_name,
        duration=appt_duration # Guardar la duración real utilizada
    )
    appointments_db.append(new_appointment)
    # Ordenar la lista para mantenerla consistente (opcional, pero buena práctica)
    appointments_db.sort(key=lambda x: (x.date, x.time))
    return new_appointment

@app.delete("/appointments/{appointment_id}", status_code=204, summary="Eliminar una cita por ID")
async def delete_appointment(appointment_id: str):
    """
    Elimina una cita específica utilizando su ID.
    """
    global appointments_db
    initial_len = len(appointments_db)
    appointments_db = [appt for appt in appointments_db if appt.id != appointment_id]
    if len(appointments_db) == initial_len:
        raise HTTPException(status_code=404, detail="Cita no encontrada.")
    return {"message": "Cita eliminada exitosamente."}

# Endpoint para la raíz
@app.get("/", summary="Mensaje de bienvenida")
async def read_root():
    return {"message": "Bienvenido a la API de Organizador de Citas. Visita /docs para la documentación de la API."}

