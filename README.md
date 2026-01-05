# generador_Unicentro
<div align="center">

<img src="logo.png" alt="Logo Unicentro" width="200"/>

# 📊 Generador de Planos Contables SIIGO
### Conciliación Automática de Cartera y Bancos | Unicentro

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![SIIGO](https://img.shields.io/badge/Compatible_con-SIIGO-orange?style=for-the-badge)
![Estado](https://img.shields.io/badge/Estado-Activo-success?style=for-the-badge)

</div>

---

## 📝 Descripción

Herramienta automatizada desarrollada para el departamento contable de **Unicentro**. Esta aplicación simplifica el proceso de conciliación bancaria cruzando los reportes de **Intereses de Cartera** contra los **Extractos Bancarios** (Bancos 9682, 9526, 0538).

El sistema genera automáticamente el archivo plano (Excel) con la estructura exacta requerida para la importación masiva de **Recibos de Caja en SIIGO**, garantizando la integridad de los datos y el manejo de consecutivos.

## 🚀 Características Principales

* **✅ Cruce Inteligente:** Algoritmo que empareja pagos por fecha, valor y ocurrencia para evitar duplicados.
* **📄 Formato SIIGO:** Genera el archivo con las +30 columnas requeridas por el software contable (Tipo R, Centros de Costo, etc.).
* **🔢 Consecutivos Automáticos:** Manejo inteligente de la numeración de recibos de caja (iniciando desde el número indicado por el usuario).
* **⚠️ Reporte de Pendientes:** Genera un archivo separado con las partidas que no cruzaron para facilitar la auditoría manual.
* **☁️ 100% Web:** No requiere instalación local gracias a Streamlit Cloud.

## 🛠️ Tecnologías Usadas

* **[Python](https://www.python.org/):** Lógica de procesamiento.
* **[Pandas](https://pandas.pydata.org/):** Manipulación y limpieza de datos (DataFrames).
* **[Streamlit](https://streamlit.io/):** Interfaz gráfica web interactiva.
* **XlsxWriter:** Motor de generación de archivos Excel.

## 📦 Estructura del Proyecto

```bash
├── app.py              # Código fuente principal de la aplicación
├── requirements.txt    # Librerías necesarias para el despliegue
├── logo.png            # Logotipo corporativo
└── README.md           # Documentación del proyecto
