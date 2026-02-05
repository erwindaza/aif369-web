# Contributing to AIF369 Website

[🇪🇸 Versión en Español](#contribuir-al-sitio-web-aif369)

Thank you for your interest in contributing to AIF369! This document provides guidelines for contributing to the project.

## 📋 Table of Contents

- [How to Contribute UI/UX Improvements](#how-to-contribute-uiux-improvements)
- [How to Contribute Code](#how-to-contribute-code)
- [How to Report Issues](#how-to-report-issues)
- [Design Guidelines](#design-guidelines)
- [Code Standards](#code-standards)

## 🎨 How to Contribute UI/UX Improvements

### Step 1: Use the Design Brief Template

We have a comprehensive template to help you structure your design proposals:

1. **Review the template**: [docs/DESIGN_BRIEF_TEMPLATE.md](./docs/DESIGN_BRIEF_TEMPLATE.md)
2. **Fill out relevant sections** - You don't need to complete every section, just the ones relevant to your proposal
3. **Add visual references** - Include links to sites you like, mockups, or sketches

### Step 2: Create an Issue

1. Go to [GitHub Issues](https://github.com/erwindaza/aif369-web/issues)
2. Click "New Issue"
3. Title format: `[Design] Brief description of your proposal`
4. In the issue body, include:
   - Your completed design brief (or relevant sections)
   - Links to visual references
   - Mockups or screenshots (if you have them)
   - Why this change would improve the site

### Step 3: Discussion

- The maintainers will review your proposal
- We may ask clarifying questions
- We'll discuss feasibility and alignment with project goals
- If approved, either you or a maintainer can implement the changes

### Example Design Proposals

**Good examples:**
- ✅ "I'd like to propose a new color scheme inspired by Stripe's recent redesign. Here's why..."
- ✅ "The mobile menu could be smoother. Here's a mockup showing a slide-in animation..."
- ✅ "Hero section could benefit from more white space. Ref: vercel.com homepage"

**What to avoid:**
- ❌ "The site looks ugly" (too vague, no actionable feedback)
- ❌ "Make it look like Apple" (too broad, no specific elements)
- ❌ Proposals without any visual references or reasoning

## 💻 How to Contribute Code

### Setup

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/aif369-web.git
cd aif369-web

# Create a branch for your changes
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Small, focused commits** - Each commit should do one thing
2. **Test your changes** - Open index.html in multiple browsers
3. **Check responsive design** - Test on mobile, tablet, desktop
4. **Maintain consistency** - Follow existing code style

### Testing Checklist

Before submitting, test on:
- [ ] Chrome Desktop
- [ ] Chrome Mobile (or use DevTools)
- [ ] Safari Desktop
- [ ] Safari iOS
- [ ] Firefox Desktop
- [ ] Edge

### Submitting Changes

```bash
# Commit your changes
git add .
git commit -m "feat: add smooth scroll animation to navigation"

# Push to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

### Pull Request Guidelines

**Title format:**
- `feat: add new feature`
- `fix: resolve issue with...`
- `style: improve button hover effects`
- `docs: update README`

**PR Description should include:**
- What changed and why
- Screenshots (for visual changes)
- Testing done
- Any breaking changes

## 🐛 How to Report Issues

### Bug Reports

Use this template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- Device: [e.g. iPhone 12, Desktop]
- OS: [e.g. iOS 15, Windows 11]
- Browser: [e.g. Chrome 95, Safari 15]
```

### Feature Requests

```markdown
**Feature Description**
A clear description of the feature you'd like.

**Problem it solves**
Explain the problem this feature would solve.

**Proposed solution**
Your suggested approach.

**Alternatives considered**
Other approaches you've thought about.

**Additional context**
Any mockups, examples, or references.
```

## 📐 Design Guidelines

### Current Design System

Review these before making design changes:
- [UI/UX Redesign Documentation](./docs/UI_UX_REDESIGN.md)
- [styles.css](./styles.css) - Check CSS variables and existing patterns

### Design Principles

1. **Simplicity** - Less is more. Avoid clutter.
2. **Consistency** - Use existing components and patterns.
3. **Performance** - Keep it fast. No heavy frameworks.
4. **Accessibility** - WCAG 2.1 AA minimum.
5. **Mobile-First** - Design for mobile, enhance for desktop.

### Color Usage

```css
/* Use existing CSS variables */
--primary: #0066FF
--secondary: #00E5CC
--accent: #7C3AED
--text-primary: #0F1419
--text-secondary: #586069
```

Only propose new colors if absolutely necessary.

### Typography

- **Headings**: Use existing size scale (clamp values)
- **Body**: 16px minimum for readability
- **Line height**: 1.6-1.7 for body text

### Spacing

Use the 8px grid system:
```css
--space-2: 0.5rem;   /* 8px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
```

### Components

Before creating new components, check if existing ones can be reused:
- Buttons (`.btn-primary`, `.btn-outline`, `.btn-link`)
- Cards (`.card`, `.card-highlight`)
- Forms (standard input/textarea styles)
- Navigation (`.site-header`, `.nav`)

## 💾 Code Standards

### HTML

- Use semantic HTML5 elements
- Include proper ARIA labels
- Add `data-i18n` attributes for translations
- Keep structure clean and readable

```html
<!-- Good -->
<article class="card">
  <h3 data-i18n="section.title">Title</h3>
  <p>Content...</p>
</article>

<!-- Avoid -->
<div class="card">
  <div class="title">Title</div>
  <div>Content...</div>
</div>
```

### CSS

- Use CSS custom properties for values used more than once
- Follow the existing naming convention
- Group related properties
- Add comments for complex rules

```css
/* Good */
.button {
  /* Layout */
  display: inline-flex;
  align-items: center;
  
  /* Spacing */
  padding: var(--space-3) var(--space-6);
  
  /* Style */
  background: var(--primary);
  border-radius: var(--radius-md);
}

/* Avoid */
.button {
  display: inline-flex;
  background: #0066FF;
  padding: 12px 24px;
  align-items: center;
  border-radius: 8px;
}
```

### JavaScript

- Use vanilla JavaScript (no jQuery)
- Comment complex logic
- Use modern ES6+ syntax
- Keep functions small and focused

```javascript
// Good
function toggleMenu() {
  const nav = document.querySelector('.nav-links');
  const isOpen = nav.classList.contains('open');
  
  nav.classList.toggle('open');
  document.body.classList.toggle('nav-open', !isOpen);
}

// Avoid
function toggle() {
  var x = document.querySelector('.nav-links');
  if (x.className.indexOf('open') > -1) {
    x.className = x.className.replace('open', '');
  } else {
    x.className += ' open';
  }
}
```

## ✅ Review Process

1. **Submission** - You submit a PR or design proposal
2. **Initial Review** - Maintainers review within 48-72 hours
3. **Discussion** - Feedback and questions
4. **Revision** - Make requested changes
5. **Approval** - Once approved, changes are merged
6. **Deployment** - Automatic deployment to production

## 🎯 Priority Areas

We especially welcome contributions in these areas:

1. **Accessibility improvements** - ARIA labels, keyboard navigation, screen reader support
2. **Performance optimization** - Reduce load time, optimize assets
3. **Mobile UX** - Improve touch interactions, responsive design
4. **Animation polish** - Smooth, delightful micro-interactions
5. **Cross-browser compatibility** - Fix issues in Safari, Firefox, Edge

## 📞 Questions?

- **Email**: erwin.daza@gmail.com
- **Issues**: [GitHub Issues](https://github.com/erwindaza/aif369-web/issues)

---

# Contribuir al Sitio Web AIF369

[🇬🇧 English Version](#contributing-to-aif369-website)

Gracias por tu interés en contribuir a AIF369! Este documento proporciona guías para contribuir al proyecto.

## 📋 Índice

- [Cómo Contribuir con Mejoras de UI/UX](#cómo-contribuir-con-mejoras-de-uiux)
- [Cómo Contribuir con Código](#cómo-contribuir-con-código)
- [Cómo Reportar Problemas](#cómo-reportar-problemas)
- [Guías de Diseño](#guías-de-diseño)
- [Estándares de Código](#estándares-de-código)

## 🎨 Cómo Contribuir con Mejoras de UI/UX

### Paso 1: Usa la Plantilla de Briefing de Diseño

Tenemos una plantilla completa para ayudarte a estructurar tus propuestas de diseño:

1. **Revisa la plantilla**: [docs/DESIGN_BRIEF_TEMPLATE.md](./docs/DESIGN_BRIEF_TEMPLATE.md)
2. **Completa las secciones relevantes** - No necesitas completar todas, solo las relevantes a tu propuesta
3. **Agrega referencias visuales** - Incluye links a sitios que te gustan, mockups o bocetos

### Paso 2: Crea un Issue

1. Ve a [GitHub Issues](https://github.com/erwindaza/aif369-web/issues)
2. Click en "New Issue"
3. Formato del título: `[Design] Descripción breve de tu propuesta`
4. En el cuerpo del issue, incluye:
   - Tu briefing de diseño completado (o secciones relevantes)
   - Links a referencias visuales
   - Mockups o capturas (si los tienes)
   - Por qué este cambio mejoraría el sitio

### Paso 3: Discusión

- Los maintainers revisarán tu propuesta
- Podemos hacer preguntas para aclarar
- Discutiremos viabilidad y alineación con objetivos del proyecto
- Si se aprueba, tú o un maintainer pueden implementar los cambios

### Ejemplos de Propuestas de Diseño

**Buenos ejemplos:**
- ✅ "Me gustaría proponer un nuevo esquema de colores inspirado en el rediseño reciente de Stripe. Aquí está el por qué..."
- ✅ "El menú móvil podría ser más suave. Aquí hay un mockup mostrando una animación slide-in..."
- ✅ "La sección hero podría beneficiarse de más espacio en blanco. Ref: homepage de vercel.com"

**Qué evitar:**
- ❌ "El sitio se ve feo" (muy vago, sin feedback accionable)
- ❌ "Hazlo ver como Apple" (muy amplio, sin elementos específicos)
- ❌ Propuestas sin referencias visuales o razonamiento

## 💻 Cómo Contribuir con Código

### Configuración

```bash
# Haz fork del repositorio en GitHub
# Clona tu fork
git clone https://github.com/TU_USUARIO/aif369-web.git
cd aif369-web

# Crea una rama para tus cambios
git checkout -b feature/nombre-de-tu-feature
```

### Haciendo Cambios

1. **Commits pequeños y enfocados** - Cada commit debe hacer una cosa
2. **Prueba tus cambios** - Abre index.html en múltiples navegadores
3. **Verifica diseño responsive** - Prueba en móvil, tablet, desktop
4. **Mantén consistencia** - Sigue el estilo de código existente

### Checklist de Pruebas

Antes de enviar, prueba en:
- [ ] Chrome Desktop
- [ ] Chrome Mobile (o usa DevTools)
- [ ] Safari Desktop
- [ ] Safari iOS
- [ ] Firefox Desktop
- [ ] Edge

### Enviando Cambios

```bash
# Commit de tus cambios
git add .
git commit -m "feat: agregar animación de scroll suave a navegación"

# Push a tu fork
git push origin feature/nombre-de-tu-feature
```

Luego crea un Pull Request en GitHub.

### Guías para Pull Requests

**Formato del título:**
- `feat: agregar nueva funcionalidad`
- `fix: resolver problema con...`
- `style: mejorar efectos hover de botones`
- `docs: actualizar README`

**La descripción del PR debe incluir:**
- Qué cambió y por qué
- Capturas de pantalla (para cambios visuales)
- Pruebas realizadas
- Cualquier cambio que rompa compatibilidad

## 🐛 Cómo Reportar Problemas

### Reportes de Bugs

Usa esta plantilla:

```markdown
**Describe el bug**
Una descripción clara del bug.

**Para Reproducir**
1. Ve a '...'
2. Click en '...'
3. Ver error

**Comportamiento esperado**
Qué esperabas que sucediera.

**Capturas de pantalla**
Si aplica, agrega capturas.

**Entorno:**
- Dispositivo: [ej. iPhone 12, Desktop]
- OS: [ej. iOS 15, Windows 11]
- Navegador: [ej. Chrome 95, Safari 15]
```

### Solicitudes de Funcionalidad

```markdown
**Descripción de la Funcionalidad**
Una descripción clara de la funcionalidad que te gustaría.

**Problema que resuelve**
Explica el problema que esta funcionalidad resolvería.

**Solución propuesta**
Tu enfoque sugerido.

**Alternativas consideradas**
Otros enfoques que has pensado.

**Contexto adicional**
Cualquier mockup, ejemplo o referencia.
```

## 📐 Guías de Diseño

### Sistema de Diseño Actual

Revisa estos antes de hacer cambios de diseño:
- [Documentación de Rediseño UI/UX](./docs/UI_UX_REDESIGN.md)
- [styles.css](./styles.css) - Revisa variables CSS y patrones existentes

### Principios de Diseño

1. **Simplicidad** - Menos es más. Evita el desorden.
2. **Consistencia** - Usa componentes y patrones existentes.
3. **Rendimiento** - Manténlo rápido. Sin frameworks pesados.
4. **Accesibilidad** - WCAG 2.1 AA mínimo.
5. **Mobile-First** - Diseña para móvil, mejora para desktop.

### Uso de Colores

```css
/* Usa variables CSS existentes */
--primary: #0066FF
--secondary: #00E5CC
--accent: #7C3AED
--text-primary: #0F1419
--text-secondary: #586069
```

Solo propón colores nuevos si es absolutamente necesario.

### Tipografía

- **Headings**: Usa la escala de tamaño existente (valores clamp)
- **Body**: 16px mínimo para legibilidad
- **Line height**: 1.6-1.7 para texto body

### Espaciado

Usa el sistema de grilla de 8px:
```css
--space-2: 0.5rem;   /* 8px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
```

### Componentes

Antes de crear componentes nuevos, verifica si los existentes pueden reutilizarse:
- Botones (`.btn-primary`, `.btn-outline`, `.btn-link`)
- Cards (`.card`, `.card-highlight`)
- Formularios (estilos estándar de input/textarea)
- Navegación (`.site-header`, `.nav`)

## 💾 Estándares de Código

### HTML

- Usa elementos semánticos HTML5
- Incluye ARIA labels apropiados
- Agrega atributos `data-i18n` para traducciones
- Mantén la estructura limpia y legible

```html
<!-- Bien -->
<article class="card">
  <h3 data-i18n="section.title">Título</h3>
  <p>Contenido...</p>
</article>

<!-- Evitar -->
<div class="card">
  <div class="title">Título</div>
  <div>Contenido...</div>
</div>
```

### CSS

- Usa propiedades personalizadas CSS para valores usados más de una vez
- Sigue la convención de nombres existente
- Agrupa propiedades relacionadas
- Agrega comentarios para reglas complejas

```css
/* Bien */
.button {
  /* Layout */
  display: inline-flex;
  align-items: center;
  
  /* Spacing */
  padding: var(--space-3) var(--space-6);
  
  /* Style */
  background: var(--primary);
  border-radius: var(--radius-md);
}

/* Evitar */
.button {
  display: inline-flex;
  background: #0066FF;
  padding: 12px 24px;
  align-items: center;
  border-radius: 8px;
}
```

### JavaScript

- Usa JavaScript vanilla (sin jQuery)
- Comenta lógica compleja
- Usa sintaxis moderna ES6+
- Mantén las funciones pequeñas y enfocadas

```javascript
// Bien
function toggleMenu() {
  const nav = document.querySelector('.nav-links');
  const isOpen = nav.classList.contains('open');
  
  nav.classList.toggle('open');
  document.body.classList.toggle('nav-open', !isOpen);
}

// Evitar
function toggle() {
  var x = document.querySelector('.nav-links');
  if (x.className.indexOf('open') > -1) {
    x.className = x.className.replace('open', '');
  } else {
    x.className += ' open';
  }
}
```

## ✅ Proceso de Revisión

1. **Envío** - Envías un PR o propuesta de diseño
2. **Revisión Inicial** - Los maintainers revisan en 48-72 horas
3. **Discusión** - Feedback y preguntas
4. **Revisión** - Haces los cambios solicitados
5. **Aprobación** - Una vez aprobado, los cambios se mergean
6. **Despliegue** - Despliegue automático a producción

## 🎯 Áreas Prioritarias

Especialmente bienvenidas contribuciones en estas áreas:

1. **Mejoras de accesibilidad** - ARIA labels, navegación por teclado, soporte para lectores de pantalla
2. **Optimización de rendimiento** - Reducir tiempo de carga, optimizar assets
3. **UX móvil** - Mejorar interacciones táctiles, diseño responsive
4. **Pulido de animaciones** - Micro-interacciones suaves y deliciosas
5. **Compatibilidad cross-browser** - Arreglar problemas en Safari, Firefox, Edge

## 📞 ¿Preguntas?

- **Email**: erwin.daza@gmail.com
- **Issues**: [GitHub Issues](https://github.com/erwindaza/aif369-web/issues)

---

**¿Listo para contribuir?** Comienza con la [Plantilla de Briefing de Diseño](./docs/DESIGN_BRIEF_TEMPLATE.md) →
