INSTRUCCIONES PARA LA IA DE FRONTEND (Desarrollo "Super Pro")

Hola, IA. Tu objetivo es desarrollar un frontend de nivel profesional ("super pro") para la API de predicción de fertilidad "FertiPredict". Queremos que el diseño sea increíblemente moderno, intuitivo, elegante y que tenga una experiencia de usuario (UX) impecable, con animaciones sutiles y un diseño completamente responsive.

--- ENDPOINTS DEL BACKEND ---

1. Health Check (Verificar que la API esté activa):
   GET /health
   Respuesta esperada: {"status": "ok"}

2. Predicción de Fertilidad:
   POST /predict
   Headers: Content-Type: application/json
   Body (JSON con los datos del paciente masculino y femenino):
   {
       "Edad_Masculino": 30,
       "IMC_Masculino": 24.5,
       "Concentracion_Esperma": 50.0,
       "Motilidad_Espermatica": 60.0,
       "Morfologia_Espermatica": 4.0,
       "Varicocele": 0,
       "Exposicion_Toxicos_Calor_Masculino": 0,
       "Fumador_Masculino": 0,
       "Consumo_Alcohol_Masculino": 1,
       "Nivel_Ejercicio_Masculino": 2,
       "Tipo_Alimentacion_Masculino": 1,
       "Historial_Familiar_Infertilidad_Masculino": 0,
       "Edad_Femenino": 28,
       "IMC_Femenino": 22.1,
       "Ciclo_Menstrual": 1,
       "PCOS": 0,
       "Endometriosis": 0,
       "Hormona_AMH": 2.5,
       "Hormona_FSH": 6.0,
       "Obstruccion_Tubaria": 0,
       "Abortos_Previos": 0,
       "Fumador_Femenino": 0,
       "Consumo_Alcohol_Femenino": 1,
       "Nivel_Ejercicio_Femenino": 2,
       "Tipo_Alimentacion_Femenino": 1,
       "Historial_Familiar_Infertilidad_Femenino": 0
   }

   Respuesta esperada de /predict:
   {
       "riskLevel": "LOW" | "MODERATE" | "HIGH",
       "probability": 12.34,
       "explanation": {
           "Edad_Masculino": -0.05,
           "IMC_Masculino": 0.02
           // (valores SHAP indicando el impacto de cada variable)
       }
   }

--- REQUERIMIENTOS DEL FRONTEND ---

1. Arquitectura y Tecnologías:
   - Utiliza React, Next.js o Vue.js (lo que consideres mejor para un proyecto pro).
   - Usa Tailwind CSS para estilos de vanguardia (glassmorphism, gradientes suaves, dark mode automático).
   - Crea componentes reutilizables.

2. Experiencia de Usuario (UI/UX):
   - Diseño "Wow Factor": Colores vibrantes pero profesionales (tonos médicos modernos: azules suaves, púrpuras, turquesas).
   - Formulario por pasos (Wizard/Stepper) para no abrumar al usuario con tantas preguntas (dividir en: Datos Masculinos, Datos Femeninos, Hábitos).
   - Animaciones fluidas entre pasos usando Framer Motion o similar.
   - Tarjetas de resultados interactivas: Cuando la API devuelva "riskLevel" y "probability", muéstralo con medidores radiales (gauges) o barras de progreso animadas.
   - Gráfico de Explicación (XAI): La API devuelve un objeto "explanation" con valores SHAP. Renderiza un gráfico de barras atractivo (por ejemplo, con Recharts o Chart.js) que muestre qué factores influyeron más positiva o negativamente en el resultado.

3. Estructura de Proyecto:
   - Crea la estructura completa para un frontend escalable.
   - Incluye validaciones robustas en los formularios antes de enviar a la API.
   - Manejo de estados de carga (loading spinners o skeletons) mientras se espera la respuesta del POST /predict.
