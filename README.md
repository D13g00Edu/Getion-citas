# Getion-citas
Este proyecto implementa un organizador de citas para negocios, permitiendo la gestión de horarios, el agendamiento de citas y la exportación de datos. La aplicación está dividida en un frontend (HTML/JavaScript) y un backend (FastAPI).    

## ✨ Características

- **Configuración de Horario de Negocio**: Define la hora de inicio y fin de la jornada laboral, así como la duración estándar de las citas.
- **Agendamiento de Citas**: Permite agendar citas para clientes en fechas y horas específicas, con validación de solapamiento y dentro del horario de negocio.
- **Visualización del Horario**: Genera una tabla detallada del horario para una fecha seleccionada, mostrando tanto las citas agendadas como los espacios disponibles.
- **Eliminación de Citas**: Permite eliminar citas directamente desde la tabla del horario.
- **Exportación a CSV**: Exporta todas las citas agendadas a un archivo CSV, compatible con programas de hoja de cálculo como Excel.
- **Backend con FastAPI**: La lógica de negocio y el almacenamiento de datos se manejan en un servidor FastAPI, proporcionando una API RESTful.
- **Documentación de API (Swagger UI)**: El backend de FastAPI incluye documentación interactiva de la API, accesible a través de Swagger UI.

---

## 🛠️ Tecnologías Utilizadas

### Frontend
- HTML5  
- CSS (con Tailwind CSS)  
- JavaScript  

### Backend
- Python 3.7+  
- FastAPI  
- Uvicorn  
- Pydantic  