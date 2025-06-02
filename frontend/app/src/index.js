import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));

const chineseBackend = process.env.REACT_APP_CHINESE_BACKEND;
// const chineseSimBackend = process.env.REACT_APP_CHINESE_SIM_BACKEND;
// const chineseTraBackend = process.env.REACT_APP_CHINESE_TRA_BACKEND;
const russianBackend = process.env.REACT_APP_RUSSIAN_BACKEND;
const defaultBackend = chineseBackend;
const ocrEndpoint = "/ocr";
const translateEndpoint = "/bulk-translate";
const databaseEndpoints = {
  saveSession: "/save-session",
  discardSession: "/delete-one-session",
  loadSession: "/load-session",
}
const languageOptions = [
  { label: "English", value: "english", backend: defaultBackend, ocrEndpoint: ocrEndpoint, translateEndpoint: translateEndpoint },
  // { label: "Chinese", value: "chinese", backend: chineseBackend, ocrEndpoint: ocrEndpoint, translateEndpoint: translateEndpoint },
  { label: "Simp. Chinese", value: "simp_chinese", backend: chineseBackend, ocrEndpoint: ocrEndpoint, translateEndpoint: translateEndpoint },
  { label: "Trad. Chinese", value: "trad_chinese", backend: chineseBackend, ocrEndpoint: ocrEndpoint, translateEndpoint: translateEndpoint },
  { label: "Russian", value: "russian", backend: russianBackend, ocrEndpoint: ocrEndpoint, translateEndpoint: translateEndpoint },
]
const imageTypeOptions = [
  { label: "Text (Paragraphs)", value: "text" },
  {label: "Text (Lines)", value: "text_lines"},
  { label: "Diagram", value: "diagram" },
  { label: "Table", value: "table" },
]
root.render(
  <React.StrictMode>
    <App languageOptions={languageOptions} imageTypeOptions={imageTypeOptions} databaseEndpoints={databaseEndpoints} />
  </React.StrictMode>
);

