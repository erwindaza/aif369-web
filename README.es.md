# AIF369 Website

[🇬🇧 English Version](./README.md)

> Equipos de IA, Datos y Cloud para empresas modernas

## 📋 Resumen

AIF369 es un sitio web de servicios profesionales que ofrece soluciones de IA, Datos y Cloud para corporaciones. Este repositorio contiene el código fuente de [aif369.com](https://aif369.com).

**Stack Tecnológico:**
- HTML5, CSS3 y JavaScript Vanilla puro (sin frameworks)
- CSS moderno con propiedades personalizadas y Grid/Flexbox
- Diseño responsive (mobile-first)
- Ligero y performante (~25KB CSS)

## 🎨 Cómo Contribuir con Mejoras de UI/UX

¡Bienvenidas las sugerencias de diseño y mejoras de UI/UX! Aquí te explicamos cómo puedes contribuir:

### Cómo Pasar una Plantilla de Diseño

Tenemos una plantilla completa de briefing de diseño que facilita compartir tus ideas:

1. **Completa la Plantilla de Briefing de Diseño**  
   → Ver [docs/DESIGN_BRIEF_TEMPLATE.md](./docs/DESIGN_BRIEF_TEMPLATE.md)
   
2. **Envía tu propuesta**
   - Crea un nuevo issue con la etiqueta `design`
   - Incluye tu briefing de diseño completado
   - Agrega referencias visuales (mockups, capturas, links)

3. **Qué incluir:**
   - Referencias visuales (sitios que te gustan y por qué)
   - Preferencias de paleta de colores
   - Sugerencias de tipografía
   - Estilos de componentes (botones, cards, formularios)
   - Preferencias de animaciones
   - Prioridades mobile/responsive

### Secciones de la Plantilla de Diseño

La plantilla cubre:
- 🎨 Referencias visuales e inspiración
- 🎨 Preferencias de paleta de colores
- ✍️ Elección de tipografía
- 📐 Layout y estructura
- 🔘 Especificaciones de componentes
- ✨ Animaciones e interacciones
- 📱 Prioridades responsive/mobile
- 🎯 Secciones específicas a mejorar

### Sistema de Diseño Actual

¿Quieres entender el diseño actual? Revisa:
- [docs/UI_UX_REDESIGN.md](./docs/UI_UX_REDESIGN.md) - Documentación completa del sistema de diseño
- [styles.css](./styles.css) - Implementación CSS con comentarios detallados

**Características actuales:**
- Diseño moderno inspirado en Linear.app y Stripe
- Variables CSS personalizadas para consistencia
- Efectos de glassmorphism
- Animaciones y transiciones suaves
- Diseño responsive mobile-first
- Accesibilidad (WCAG 2.1 AA)

## 🚀 Inicio Rápido

### Ver el sitio localmente

```bash
# Clonar el repositorio
git clone https://github.com/erwindaza/aif369-web.git
cd aif369-web

# Abrir en navegador (¡no requiere build!)
open index.html
# o usar un servidor local:
python -m http.server 8000
# Luego visitar http://localhost:8000
```

### Estructura del Proyecto

```
aif369-web/
├── index.html              # Página principal
├── services.html           # Vista de servicios
├── education.html          # Contenido educativo
├── blog.html              # Listado de blog
├── blog-post-*.html       # Posts individuales
├── portfolio.html          # Portafolio/casos de estudio
├── product.html           # Página de producto IA
├── styles.css             # Hoja de estilos principal
├── scripts.js             # Funcionalidad JavaScript
├── docs/                  # Documentación
│   ├── DESIGN_BRIEF_TEMPLATE.md
│   ├── UI_UX_REDESIGN.md
│   └── ...
├── backend/               # Servicios backend
└── infra/                 # Configuración de infraestructura
```

## 🤝 Contribuir

¡Bienvenidas las contribuciones! Aquí hay formas en que puedes ayudar:

### Diseño y UI/UX
- Enviar propuestas de diseño usando la [Plantilla de Briefing](./docs/DESIGN_BRIEF_TEMPLATE.md)
- Reportar bugs de UI o inconsistencias
- Sugerir mejoras de UX
- Probar en diferentes dispositivos y navegadores

### Código
- Corregir bugs
- Mejorar accesibilidad
- Optimizar rendimiento
- Agregar nuevas funcionalidades

### Contenido
- Corregir errores ortográficos o gramaticales
- Mejorar traducciones (ES/EN)
- Sugerir mejor copy

Por favor ver [CONTRIBUTING.md](./CONTRIBUTING.md) para guías detalladas.

## 📚 Documentación

- **[Plantilla de Briefing de Diseño](./docs/DESIGN_BRIEF_TEMPLATE.md)** - Cómo enviar propuestas de diseño
- **[Rediseño UI/UX](./docs/UI_UX_REDESIGN.md)** - Documentación del sistema de diseño actual
- **[Configuración de Email](./docs/EMAIL_SETUP.md)** - Configuración de email backend
- **[Roadmap de Arquitectura](./docs/ARCHITECTURE_ROADMAP.md)** - Roadmap técnico

## 🎯 Filosofía de Diseño

Nuestros principios de diseño:
- **Simple y Profesional** - Layouts limpios que dejan brillar el contenido
- **Rendimiento Primero** - Sin frameworks o librerías innecesarias
- **Accesible** - Cumplimiento mínimo WCAG 2.1 AA
- **Mobile-First** - Gran experiencia en todos los dispositivos
- **Moderno y Atemporal** - Diseño contemporáneo que no envejece

## 🌐 Despliegue

El sitio se despliega automáticamente a producción en cada push a `main`:
- **Producción**: [aif369.com](https://aif369.com)
- **Plataforma**: Vercel
- **Preview**: URLs de preview automáticas para pull requests

## 📄 Licencia

© 2026 AIF369 SpA - Chile. Todos los derechos reservados.

## 📞 Contacto

- **Sitio web**: [aif369.com](https://aif369.com)
- **Email**: erwin.daza@gmail.com
- **Issues**: [GitHub Issues](https://github.com/erwindaza/aif369-web/issues)

---

**¿Quieres mejorar el diseño?** Comienza con la [Plantilla de Briefing de Diseño](./docs/DESIGN_BRIEF_TEMPLATE.md) →
