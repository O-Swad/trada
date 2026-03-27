# Contexto
Necesito hacer un trade-off para un sistema de misión software de un avión de patrulla marítima, DAL-E, comparando su implementación basada como Platform as a Service (PaaS) versus No PaaS. Para ello, quiero usar una serie de variables cualitativas, con unas puntuaciones y pesos, así como unos escenarios. Quiero una aplcación web que me permita configurar diferentes pesos de las variables a considerar y con ello ver como cambian las métricas a evaluar y los gráficos asociados. En esencia quiero una aplciación web para poder crear trade-offs.

# Requisitos funcionales
1. Quiero que la aplicación sea genérica, de tal modo que pueda servir para cualquier trade-off entres dos o más opciones a futuro.
2. Quiero poder añadir atributos cualitativos, poder darles un nombre, una descripción y un peso en valor real.
	2.1 Quiero que se vallan añadiendo a una tabla que permita ir viendo que atributos van a ser comparados.
3. Quiero poder añadir escenarios en los para poder comparar las opciones de trade-off bajo estudio.
	3.1 Se ha de poder añadir el nombre del escenario y su descripción.
4. Se ha de poder añadir las escalas de los pesos asignados y del scoring.
	4.1 Se han de poder crear nuevas escalas para ponderar escenarios y variables.
	4.2 Cuando se crea una escala se tiene que poder añadir para cada uno de los valores una descripción para especificar que significa. Por ejemplo: Score:1, Meaning: Low Cost.
	4.3 Todas las escalas tienen que aparecer en forma de tabla. 
	4.4 Añadir un nuevo valor es añadir una nueva fila a la tabla. 
5. Tengo que poder añadir nuevas fórmulas para calcular los índices o fórmulas por las que voy a comparar.
	5.1 A tales fórmulas quiero poder darles un nombre descriptivo del valor que calculan.
6. Por defecto quiero que se puedan calcular como mínimo las siguientes métricas de comparación:
	6.1 Architectural Benefit Score (ABS), cuya fórmula es el sumatorio(GlobalWeight*Score(A,S_i), siendo el GlobalWeight=AttributeWeight_i * LocalWeight_i. A es la alternativa (PaaS, NoPaaS) y S_i es el score para la alternativa A correspondiente.
	6.2 Benefit to Cost and Risk Index o Trade Index, que se calcula como T(A)= ABS(A)/(alpha*Cost(A)+beta*Risk(A)). Alpha y beta son pesos normalizados(alpha+beta=1) del Coste y del Riesgo. Ambos pesos tienen que poder ser introducidos por el usuario en una tabla de valores para poder comparar los resultados ante diferentes valores de los pesos y ver como progresan las métricas en un gráfico. Cost y Risk son variables configurables de acuerdo a una escala como las citadas anteriormente.

7. Quiero poder introducir distintos valores en una tabla para ir comparando como cambia el resultado del trade.
8. Quiero poder hacer análisis de sensibilidad (ejemplo: Sensitivity to weight of Risk, sensitivity to weight of "evolbability)
9. Las operaciones básicas que tengo que poder hacer para hacer análisis trade-of son las siguientes:
	9.1 Poder crear tablas para introducir datos.
	9.2 Poder crear tablas para introducir pesos.
	9.3 Poder crear tablas para introducir Scores.
	9.4 Poder añadir métricas y sus fórmulas.
	9.5 Poder ver gráficos de evolución en función de los distintos valores de unos y otros.
	9.6 Quiero que la interfaz sea usable y accesible y cumpla con principios UX. Con colores y contrastes adecuados. Quiero una GUI profesional. 

# Requisitos no funcionales
10. Ha de ser una aplicación web para poder desplegarla y que la puedan consumir mis compañeros de trabajo.
11. Quiero que implementes la APP usando Python Reflex.
12. Documenta el código fuente.
13. Haz una arquitectura de software simple pero cumpliendo los principios SOLID. Nada de overengineering.
14. Genera documentación de uso.
