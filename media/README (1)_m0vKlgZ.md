# Currency Converter 
Convert currencies instantly with a responsive live exchange rate dashboard and local weather insights.

**View Site** → [Currency Converter](https://tech-stack-hub-lab.github.io/currency-converter/)
![Screenshot of the dark mode on different devices](assets/documents/mockup1.jpeg)
![Screenshot of the light mode on different devices](assets/documents/mockup2.jpeg)

## 📚 Table of Contents

- [📌 Project Overview](#-project-overview)
- [📁 Project Structure](#-project-structure)
- [🎯 User Stories](#-user-stories)
- [🚀 Features](#-features)
- [🖥️ Technologies Used](#️-technologies-used)
- [🎨 Front-End Design & Interactivity (LO1)](#-front-end-design--interactivity-lo1)
  - [Colour Palette](#colour-palette)
  - [Typography](#typography)
  - [Wireframes](#wireframes)
- [✅ Testing & Validation (LO2)](#-testing--validation-lo2)
- [☁️ Deployment & Version Control (LO3)](#️-deployment--version-control-lo3)
- [📚 Documentation & Code Quality (LO4)](#-documentation--code-quality-lo4)
- [⚙️ JavaScript Functionality (LO5)](#️-javascript-functionality-lo5)
- [🤖 AI Usage & Reflection (LO6)](#-ai-usage--reflection-lo6)
- [📦 Installation & Setup](#-installation--setup)
- [🚀 Deployment Instructions](#-deployment-instructions)
- [📸 Screenshots](#-screenshots)
- [🔗 API Attribution](#-api-attribution)
- [🚀 Future Improvements](#-future-improvements)
- [Lighthouse Performance](#lighthouse-performance)

---

# 📌 Project Overview

Currency Converter is a responsive single-page web application built to convert currencies with real-time exchange data and weather context. The design focuses on clean layout, responsive behavior, and fast user interaction across desktop, tablet, and mobile.

# 📁 Project Structure


currency-converter/
├── index.html
├── assets/
│   ├── css/style.css
│   ├── js/script.js
│   ├── images/
│   ├── json/currency.json
│   
└── README.md

## 🧾 User Stories

### 🌙 Theme Feature
- As a user, I want to toggle between dark and light mode so that I can use the app comfortably in different lighting conditions.
- As a returning user, I want my theme preference saved so that I don’t need to change it every time.

---

### 💱 Currency Converter
- As a user, I want to convert currencies in real time so that I can quickly check exchange values.
- As a user, I want to select different currencies so that I can convert between any countries.
- As a user, I want to see the conversion rate and last updated time so that I can trust the accuracy.

---

### 🔄 Swap Function
- As a user, I want to swap currencies instantly so that I can save time when reversing conversions.

---

### 📊 Chart Feature
- As a user, I want to see exchange rate trends in a chart so that I can understand currency changes over time.
- As a user, I want to change the time range (week/month/year) so that I can analyse trends easily.

---

### 🌦️ Weather Feature
- As a user, I want to see my local weather so that I can stay informed without leaving the app.
- As a user, I want clear weather icons and temperature so that the data is easy to understand.

---

### 📂 Currency List / Cards
- As a user, I want to browse available currencies so that I can learn about different world currencies.
- As a user, I want country-based currency lists to load incrementally ("Load More") so that the page stays clean and performs well.

---

### ℹ️ About Section
- As a user, I want a "Read more" option in the About section so that I can expand details progressively without overwhelming the page.

---

### ⚠️ Error Handling
- As a user, I want clear error messages when I enter invalid input so that I know how to fix it.
- As a user, I want the app to handle API errors smoothly so that it doesn’t crash.

Additional notes on API errors and CORS:

- The chart feature is intended to support multiple historical ranges (day, week, month, year, 5-year). During frontend development the project encountered CORS restrictions when calling the historical exchange-rate API directly from the browser with an API key. Because the API rejects cross-origin requests, the frontend currently requests only weekly data as a permitted workaround.
- Current fallbacks and mitigations:
  - Weekly chart data is shown in the frontend to keep the chart usable during development.
  - Country and currency lists are loaded from `assets/json/currency.json` to avoid repeated API requests and improve performance.
  - API errors are surfaced to the user with friendly guidance to retry or check connectivity.

- Planned permanent solution:
  - Implement a small backend (Node/Express, serverless function, or similar) to proxy historical API requests, securely store the API key, and avoid CORS issues. The backend will aggregate historical ranges (day/week/month/year/5-year) and expose endpoints the frontend can safely consume.
  - After a backend proxy is available, the chart will be extended to support selectable time ranges with full historical data.

---

### 📱 Responsiveness & Navigation
- As a mobile user, I want the app to work on my device so that I can use it anywhere.
- As a user, I want smooth navigation so that I can move between sections easily.


# 🚀 Features

- Live currency conversion and swap controls
- Weather panel with conditions, temperature, and feels-like data
- Responsive chart section for exchange trends (currently limited to weekly data in the frontend)
- Uses a local `assets/json/currency.json` for the country/currency list to improve performance and reduce API calls
- Country currency overview cards
- About section with informative layout
- Expandable FAQ-style panels for user information
- Light/dark ready interface structure
- Clean navigation and accessible mobile menu behavior

# 🖥️ Technologies Used

- HTML5 for semantic structure
- CSS3 for responsive styling and layout
- JavaScript (ES6) for interactivity and API integration
- Bootstrap 5 for grid responsiveness and components
- Font Awesome for icons and UI markers
- Chart.js for trend visualization support
- OpenWeather API for weather data
- Exchange rate API for currency values
- LocalStorage for theme and state persistence

# 🎨 Front-End Design & Interactivity (LO1)

The UI emphasizes a modular dashboard with clear sections and responsive grouping.

## Colour Palette

**Dark mode**

![Currency Converter](assets/documents/dark-mode.png)

**Light mode**

![Currency Converter](assets/documents/light-mode.png)


## Typography

- Simple, readable text hierarchy
- Bold headings for section titles and UI labels
- Smaller body text for field and helper content
- Responsive typography sizing across breakpoints
The project uses one display family from [Google Fonts](https://fonts.google.com/share?selection.family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900|Roboto+Serif:ital,opsz,wght@0,8..144,100..900;1,8..144,100..900), loaded in `index.html`.

## Wireframes

The wireframes show desktop, tablet, and mobile layout structure with the updated screenshot-style design.

![Wireframes](assets/documents/wireframes/screens.png)

These wireframes are stored in `assets/documents/wireframes` and reflect the key homepage sections: navigation, converter hero, weather panel, exchange chart, currency cards, about section, FAQ, and footer.

# ✅ Testing & Validation (LO2)

- HTML structure is built with semantic elements and validated for correctness
![validation](assets/documents/validation-result/html-validation.png)
- CSS is structured for responsive rendering and minimal duplication
![validation](assets/documents/validation-result/css-validation.png)
- JavaScript behavior is tested to ensure no syntax errors and proper form handling
![validation](assets/documents/validation-result/javascript-validation.png)

# ☁️ Deployment & Version Control (LO3)

- Project is prepared for GitHub Pages deployment
- Source code is tracked using Git
- Commit history should reflect incremental updates and wireframe improvements
- Deployment can be published from the `main` or `gh-pages` branch for live hosting

# 📚 Documentation & Code Quality (LO4)

- Code organization separates `index.html`, `assets/css/style.css`, and `assets/js/script.js`
- Comments are used to document major sections and interactive behavior
- File paths are consistent and static assets are grouped clearly
- README contains an overview, feature summary, and setup instructions



# 🤖 AI Usage & Reflection (LO6)

AI tools were used as an assistive resource throughout this project. Their use focused on suggestion, verification, and content generation while retaining human oversight. Key uses:

- Drafting and polishing README text, user stories, and section headings.
- Generating wireframe and mockup concepts that informed layout decisions.
- Checking JavaScript logic and suggesting improvements (I asked the AI to review functions and then validated changes manually).
- Proposing accessibility, responsiveness, and UX improvements.
- Suggesting test cases, validation checks, and debugging approaches.
- Producing concise commit-message and documentation drafts.

Responsible use and limitations:

- AI output was used as recommendations only; every code change and design decision was reviewed and tested by me before inclusion.
- I did not share any sensitive or private data with the AI.
- Where the AI influenced visuals or copy, I edited for accuracy, clarity, and consistency with project goals.

Example prompts:

 - "Check this currency conversion function for logic errors and suggest improvements."
 - "Create wireframe ideas for a currency-converter dashboard with weather panel."

# 📦 Installation & Setup

Clone the repository:

```bash
git clone https://github.com/your-username/currency-converter.git
cd currency-converter
```

Open the project in a browser or use VS Code Live Server for local development.

# 🚀 Deployment Instructions

1. Push code to GitHub
2. Open repository settings
3. Select Pages
4. Choose the branch to deploy from (`main` or `gh-pages`)
5. Save and copy the generated live URL

# 📸 Screenshots

Use the wireframe images above for the updated responsive layout preview.
![Desktop]
![Screenshot of the dark mode on desktop](assets/documents/desktop/1.jpeg)
![Screenshot of the light mode on desktop](assets/documents/desktop/2.jpeg)

![Tablet]
![Screenshot of the dark mode on tablet](assets/documents/tablet/tablet2.jpeg)
![Screenshot of the light mode on tablet](assets/documents/tablet/tablet1.jpeg)

![Mobile]
![Screenshot of the dark mode on mobile](assets/documents/mobile/1.png)
![Screenshot of the light mode on mobile](assets/documents/mobile/2.png)
# 🔗 API Attribution

- OpenWeatherMap for weather data
- ExchangeRate API for currency conversion rates

# 🚀 Future Improvements

- Add currency favorites and bookmarks
- Improve chart with real historical API data (backend proxy to resolve CORS and secure API keys; support day/week/month/year/5-year ranges)
- Add multi-language support
- Enhance accessibility and keyboard navigation
- Add offline caching for faster load times

# Lighthouse Performance

- Performance: optimized asset structure and minimal resource overhead
- Accessibility: semantic HTML, readable contrast, and keyboard-friendly controls
- Best Practices: modern resource loading via CDN and structured code
- SEO: meta descriptions, titles, and meaningful content hierarchy

> Recommended: run Chrome Lighthouse for exact desktop and mobile scores.
![lighthouse](assets/documents/validation-result/accessibility.png)
