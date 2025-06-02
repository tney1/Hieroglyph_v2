import { useState, useEffect } from "react";
import Button from 'react-bootstrap/Button';
import Alert from 'react-bootstrap/Alert';
import Spinner from 'react-bootstrap/Spinner';
import { useImperativeFilePicker } from 'use-file-picker';
import {
    FileAmountLimitValidator,
    FileTypeValidator,
} from 'use-file-picker/validators';
import axios from 'axios';
import sha256 from 'crypto-js/sha256'
import Base64 from 'crypto-js/enc-base64'
import Dropdown from 'react-bootstrap/Dropdown';
import { jsPDF } from 'jspdf';

function AlertDismissable({ errorContent, showAlert, setShowAlert }) {
    return (
        <>
            <Alert style={{position: "fixed", top: 0, width: "100%"}} show={showAlert} onClose={() => setShowAlert(false)} variant="warning" dismissible>
                <Alert.Heading>Hieroglyph Error</Alert.Heading>
                <p>{errorContent}</p>
            </Alert>
        </>
    )
}


function OCRButton({ callback, gatherStage1Data, languageOptions, selectedLanguage, readyTriggers, errorLogger }) {
    console.log(`StageButtons.OCRButto.n RERENDER stage OCR props:`, languageOptions);

    const [isLoading, setLoading] = useState(false);
    const [sendAllPages, setSendAllPages] = useState(false);

    const ocrAll = () => {
        console.log("StageButtons.OCRButton: ocrAll SETTING LOADING TO TRUE");
        setLoading(true);
        setSendAllPages(true);
    }
    const ocrCurrent = () => {
        console.log("StageButtons.OCRButton: ocrCurrent SETTING LOADING TO TRUE");
        setLoading(true);
        setSendAllPages(false);
    }

    const stageSubmit = async () => {
        const requestData = await gatherStage1Data(sendAllPages)
        if (!requestData) {
            console.error("StageButtons.OCRButton: Submit data confirming no data to post: ", requestData);
            errorLogger(`No data to submit: ${requestData instanceof Object ? JSON.stringify(requestData) : requestData}`);
            return Promise.reject("No data to submit");
        } else {
            console.debug("StageButtons.OCRButton: Request data looks like", requestData)
        }
        const languageOption = languageOptions.filter((lang) => lang.value === selectedLanguage)[0]
        console.log(`StageButtons.OCRButton: stage OCR SELECTED:`, languageOption);
        
        let allNewData = []
        for (const pageData of requestData) {
            console.log(`StageButtons.OCRButton: Submitting to ${languageOption.backend + languageOption.ocrEndpoint}, data to post:`, pageData);
            const data = await axios.post(languageOption.backend + languageOption.ocrEndpoint, pageData).then((response) => {
                console.log('StageButtons.OCRButton: Raw Response via stageSubmitOCR is:', response.data[0], typeof response.data[0]);
                allNewData.push(response.data[0])
                console.log(`StageButtons.OCRButton: STATUS ${response.status} via stageSubmitOCR is:`, allNewData);
            }).catch(function (error) {
                console.error(error);
                errorLogger(`OCRButton: API Bad response: ${error instanceof Object ? JSON.stringify(error) : error}`);
                return Promise.reject(`OCRButton: API Bad response: ${error instanceof Object ? JSON.stringify(error) : error}`);
            });
        }
        console.log("StageButtons.OCRButton: OCR returning ", allNewData)
        return allNewData;
        // return resolve(allNewData);
    };

    useEffect(() => {
        console.log("StageButtons.OCRButton: OCR Use effect triggered: ");
        if (isLoading) {
            console.log('StageButtons.OCRButton: OCR SETTING LOADING: pre submit');
            stageSubmit().then((data) => {
                console.log("StageButtons.OCRButton: SETTING LOADING TO FALSE", data);
                setLoading(false);
                console.log("StageButtons.OCRButton: Callback:", callback);
                callback(data);
                clearTimeout();
            }).catch(function (error){
                console.error("StageButtons.OCRButton: setting loading Stage submit error:", error);
                setLoading(false);
                errorLogger(`OCR Failed: ${error instanceof Object ? JSON.stringify(error) : error}`)
                clearTimeout();
            });
            console.log('StageButtons.OCRButton: OCR returned after stagesubmit');
        }
    }, [isLoading]); //, callback, errorLogger, stageSubmit]);

    return (
        <Dropdown style={{ marginLeft: "0", marginBottom: ".5em" }}>
            <Dropdown.Toggle variant="primary" size="sm" disabled={isLoading || !readyTriggers}>{isLoading ? <Spinner as="span" animation="border" size="sm" role="status" /> : "OCR"}</Dropdown.Toggle>
            <Dropdown.Menu>
                <Dropdown.Item onClick={!isLoading ? ocrCurrent : null}>OCR Current Page</Dropdown.Item>
                <Dropdown.Item onClick={!isLoading ? ocrAll : null}>OCR All Pages</Dropdown.Item>
            </Dropdown.Menu>
        </Dropdown>
        //<Button  className='pageButtons' onClick={!isLoading ? ocrCurrent : null} variant='primary' style={{ marginLeft: "0", marginBottom: ".5em" }} disabled={isLoading || !readyTriggers} >{isLoading ? <Spinner as="span" animation="border" size="sm" role="status" /> : "Process Current Page"}</Button>
    );
}



function TranslateButton({ callback, triggerDataUpdate, gatherStage2Data, languageOptions, selectedLanguage, selectedSecondLanguage, readyTriggers, errorLogger }) {
    console.log(`StageButtons.TranslateButton: RERENDER stage translate props:`, languageOptions);

    const [isLoading, setLoading] = useState(false);
    const [sendAllPages, setSendAllPages] = useState(false);

    const translateAll = () => {
        console.log("StageButtons.TranslateButton: translateAll SETTING LOADING TO TRUE");
        triggerDataUpdate();
        setLoading(true);
        setSendAllPages(true);
    }
    const translateCurrent = () => {
        console.log("StageButtons.TranslateButton: translateCurrent SETTING LOADING TO TRUE");
        triggerDataUpdate();
        setLoading(true);
        setSendAllPages(false);
    }

    const stageSubmit = async () => {
        const requestData = await gatherStage2Data(sendAllPages);
        if (!requestData) {
            console.error("StageButtons.TranslateButton: Submit data confirming no data to post: ", requestData);
            errorLogger(`Translate Failed: No data to submit: ${requestData instanceof Object ? JSON.stringify(requestData) : requestData}`);
            return Promise.resolve();
        } else {
            console.debug("StageButtons.TranslateButton: Request data looks like", requestData)
        }
        
        const languageOption = languageOptions.filter((lang) => lang.value === selectedLanguage)[0]
        console.log(`StageButtons.TranslateButton: STAGESUBMIT stage Translate SELECTED:`, languageOption);

        let allNewData = {}
        console.log(`StageButtons.TranslateButton: Submitting to ${languageOption.backend + languageOption.translateEndpoint}, data to post:`, requestData);
        const data = await axios.post(languageOption.backend + languageOption.translateEndpoint, requestData).then((response) => {
            console.log(`StageButtons.TranslateButton: STATUS ${response.status} via stageSubmitTranslate is:`, response.data);
            allNewData = {...response.data}
            console.log("StageButtons.TranslateButton: Returned all new data from request for page data", allNewData)
            // return allNewData;
        }).catch(function (error) {
            console.error(error);
            errorLogger(`TranslateButton: API Bad response: ${error instanceof Object ? JSON.stringify(error) : error}`);
            return Promise.reject();
        });
        console.log("StageButtons.TranslateButton: stageSubmit translate returning ", allNewData)
        return allNewData;
    };
    console.log(`StageButtons.TranslateButton: PreUseEffect Stage: Translate`);
    useEffect(() => {
        console.log("StageButtons.TranslateButton: Stage: Translate Use effect backend: ");
        if (isLoading) {
            console.log(`StageButtons.TranslateButton: Stage: Translate SETTING LOADING: pre submit`);
            stageSubmit().then((data) => {
                console.log("StageButtons.TranslateButton: SETTING LOADING TO FALSE", data);
                setLoading(false);
                callback(data);
                clearTimeout();
            }).catch(function (error){
                console.error("StageButtons.TranslateButton: setting loading Stage submit error", error);
                setLoading(false);
                clearTimeout();
            });
            console.log(`StageButtons.TranslateButton: Stage: Translate returned`);

        }
    }, [isLoading]); //, callback, stageSubmit]);

    return (
        <Dropdown style={{ marginLeft: "0", marginBottom: ".5em" }}>
            <Dropdown.Toggle variant="primary" size="sm" disabled={isLoading || !readyTriggers || selectedLanguage === 'english'}>{isLoading ? <Spinner as="span" animation="border" size="sm" role="status" /> : "Translate"}</Dropdown.Toggle>
            <Dropdown.Menu>
                <Dropdown.Item onClick={!isLoading ? translateCurrent : null}>Translate Current Page</Dropdown.Item>
                <Dropdown.Item onClick={!isLoading ? translateAll : null}>Translate All Pages</Dropdown.Item>
            </Dropdown.Menu>
        </Dropdown>
        // translateAll was previously disabled
        //<Button variant="primary" onClick={!isLoading ? translateCurrent : null} disabled={isLoading || !readyTriggers || selectedLanguage === 'english'}>{isLoading ? <Spinner as="span" animation="border" size="sm" role="status" /> : "Translate"}</Button>

    );
}



function ClearStagesButton({ setAllPages, setDocumentHash, setSelectedFile, setDataToExport }) {
    console.log("StageButtons.RERENDER ClearStagesButton");

    const handleClick = () => {
        console.log("StageButtons.Clearing pageData")
        setAllPages({})
        console.log("StageButtons.Clearing Selected File and Content");
        setSelectedFile(null);
        setDataToExport(false);
        setDocumentHash("");
    }
    return (<>
        <Button className='pageButtons' id="clearButton" onClick={handleClick} variant="danger">Clear Stages</Button>
    </>);
}


async function calculateDocumentHash(documentString) {
    // console.debug("StageButtons.calculateDocumentHash documentString:", documentString);
    const hash = Base64.stringify(sha256(documentString));
    console.debug("StageButtons.calculateDocumentHash Hash:", hash, typeof hash);
    return hash;
}


function SelectFileButton({ selectedFile, setSelectedFile, setDocumentHash, errorLogger, apiCheckLoadData, setAllPages }) {
    console.log("StageButtons.RERENDER SelectFileButton");
    const handleFileSelected = async (file) => {
        if (file.name.endsWith(".pdf")) {
            console.log("StageButtons.SelectFileButton, found document:")
            setSelectedFile({ name: file.name, content: file.content, isDocument: true });
        } else if (file.name.endsWith(".txt") || /\.(txt|py|java|jsx|c|cpp|h|cs|rb|php|js|ts|tsx|go|swift|kt|rs|dart|asm|sh|bat|pl|lua|r|m|vb|scala|html|htm|xml|json|yaml|yml|ini|cfg|toml|env|properties|md|rst|log|csv|tsv|tex|rtf|makefile|cmake|gradle|pom|build|gitignore|gitattributes|gitmodules|sql|ps1|xsl|xslt|scss|less|config|dat|tmpl|tpl)$/i.test(file.name))   { // || /\.(\w+)$/i.test(file.name) 

            const decodedContent = atob(file.content.split(',')[1]);
            const isReadableText = /^[\x20-\x7E\s]*$/.test(decodedContent);

            if (isReadableText){
                console.log("StageButtons.SelectFileButton, found text-based file:"); 

                const doc = new jsPDF(); // Create a new jsPDF instance 
                const lines = decodedContent.split('\n'); // Split into lines for page formatting
    
                const fontSize = 2; 
                const margin = 12; // Margin from the edges of the page 
                const pageWidth = doc.internal.pageSize.width //- margin * 2; // Width of the page minus margins 
                const pageHeight = doc.internal.pageSize.height //- margin; // Height of the page minus margins 
                let y = margin; // Start at the top margin 

                for (const line of lines) { 
                    const wrappedLines = doc.splitTextToSize(line, pageWidth); // Automatically wrap text to fit the page width 
                    for (const wrappedLine of wrappedLines) { 
                        if (y + fontSize > pageHeight+margin) { // If we're near the bottom of the page, add a new page 
                            doc.addPage(); 
                            y = margin; // Reset y position for the new page 
                        } 
                        doc.text(wrappedLine, margin, y); // Draw the text at the current position 
                        y += fontSize + 12; // Move down for the next line 
                    } 
                } 
                const pdfBase64 = doc.output('dataurlstring'); // Export the PDF as a Base64 string 
                setSelectedFile({ name: file.name.replace(/\.[^/.]+$/, ".pdf"), content: pdfBase64, isDocument: true }); 
            }

        } else {
            console.log("StageButtons.SelectFileButton, found image:")
            setSelectedFile({ name: file.name, content: file.content, isDocument: false });
        }
        calculateDocumentHash(file.content).then(
            (docStr) => {
                console.log("StageButtons.SelectFileButton DocumentHash from SelectFileButton", docStr);
                setDocumentHash(docStr);
                console.log("StageButtons.SelectFileButton set");
                apiCheckLoadData(docStr);
                console.log("StageButtons.SelectFileButton checked");
            }
        );
        setAllPages({});
    }
    
    // eslint-disable-next-line
    const { openFilePicker, filesContent } = useImperativeFilePicker({
        readAs: 'DataURL',
        accept: 'image/*,application/pdf,text/plain,text/*, .pdf,.png,.jpeg,.txt,.py,.java,.c,.cpp,.h,.cs,.rb,.php,.js,.jsx,.ts,.tsx,.go,.swift,.kt,.rs,.dart,.asm,.sh,.bat,.pl,.lua,.r,.m,.vb,.scala,.html,.htm,.xml,.json,.yaml,.yml,.ini,.cfg,.toml,.env,.properties,.md,.rst,.log,.csv,.tsv,.tex,.rtf,.makefile,.cmake,.gradle,.pom,.build,.gitignore,.gitattributes,.gitmodules,.sql,.ps1,.xsl,.xslt,.scss,.less,.config,.dat,.tmpl,.tpl',
        multiple: false,
        validators: [
            new FileAmountLimitValidator({ max: 1 }),
            new FileTypeValidator(['jpg', 'JPG', 'jpeg', 'JPEG', 'pdf', 'PDF', 'png', 'PNG', 'txt', 'TXT', 'text/*', 'py', 'java', 'c', 'cpp', 'h', 'cs', 'rb', 'php', 'js', 'jsx', 'ts', 'tsx', 
                'go', 'swift', 'kt', 'rs', 'dart', 'asm', 'sh', 'bat', 'pl', 'lua', 'r', 'm', 'vb', 'scala', 'html', 'htm', 'xml', 'json', 'yaml', 'yml', 'ini', 'cfg', 'toml', 'env', 'properties', 
                'md', 'rst', 'log', 'csv', 'tsv', 'tex', 'rtf', 'makefile', 'cmake', 'gradle', 'pom', 'build', 'gitignore', 'gitattributes', 'gitmodules', 'sql', 'ps1', 'xsl', 'xslt', 'scss', 'less', 'config', 'dat', 'tmpl', 'tpl']), // add additional file types here
        ],
        onFilesSelected: ({ plainFiles, filesContent, errors }) => {
            // this callback is always called, even if there are errors
            console.log('StageButtons.onFilesSelected', plainFiles, filesContent, errors);
        },
        onFilesRejected: ({ errors }) => {
            // this callback is called when there were validation errors
            console.log('StageButtons.onFilesRejected', errors, errors instanceof Object);
            errorLogger(`Error selecting file: ${errors instanceof Object ? JSON.stringify(errors) : errors}`)
        },
        onFilesSuccessfullySelected: ({ plainFiles, filesContent }) => {
            // this callback is called when there were no validation errors
            console.log('StageButtons.onFilesSuccessfullySelected', plainFiles, filesContent);
            console.log("StageButtons.Files content mapping for index", filesContent);
            handleFileSelected(filesContent.at(-1));
        },
        onClear: () => {
            // this callback is called when the selection is cleared
            console.log('StageButtons.onClear');
        },
        onFileRemoved: (removedFile, removedIndex) => {
            console.log("StageButtons.Removed", removedFile, removedIndex);
        }
    });
    return (
        <div>
            <Button className='pageButtons' id="selectFileButton" variant="primary" onClick={openFilePicker}>Select File</Button>
            <span>File: <span className='selectedFile'>{selectedFile ? selectedFile.name : ''}</span></span>
        </div>
    )
}
export { OCRButton, TranslateButton, ClearStagesButton, SelectFileButton, AlertDismissable };