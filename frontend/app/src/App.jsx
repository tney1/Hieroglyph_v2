import {React, useState} from 'react';

import Homepage from './components/Homepage';
import {AlertDismissable} from './components/StageButtons';

import 'bootstrap/dist/css/bootstrap.min.css';
import './styles.css'; // Import the styles.css file

function App({ databaseEndpoints, languageOptions, imageTypeOptions }) {
  const [errorContent, setErrorContent] = useState("");
  const [showAlert, setShowAlert] = useState(false);
  const errorLogger = (errorMessage) => {setErrorContent(errorMessage); setShowAlert(true)};

  return (
    <>
      <Homepage languageOptions={languageOptions} imageTypeOptions={imageTypeOptions} errorLogger={errorLogger} databaseEndpoints={databaseEndpoints} />
      <AlertDismissable errorContent={errorContent} showAlert={showAlert} setShowAlert={setShowAlert}/>
    </>
  );
}
export default App;
