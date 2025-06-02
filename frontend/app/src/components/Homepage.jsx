import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import DocumentViewer from './DocumentViewer';
// import handleDocumentLoadSuccess from './DocumentViewer';
// import goToPage from './DocumentViewer';
// import XLSX from 'xlsx';

import Accordion from 'react-bootstrap/Accordion';
import { MenuBar } from './MenuBar';
import { ExportModal } from './Export';
import { downloadPicture } from '../utilities/export';
// import { Canvas } from './Canvas';
// import callTimes from './DocumentViewer'
// import  clearCurrentPageBoxes  from './DocumentViewer';
import { jsPDF } from "jspdf"; 



import {
    TranslateButton, ClearStagesButton,
    SelectFileButton,  OCRButton
} from './StageButtons';
import { Content, Scale, LanguageDropdown, ImageTypeDropdown, updateAllTextFromContent } from './StageInput';
import { LoadModal } from './LoadSave';
//import { useState } from 'react';
import axios from 'axios';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

import React, {useState, useEffect} from 'react'; // not using these at the moment (useEffect, useCallback, useRef)
// import {Document, Page} from 'react-pdf';
// import {createRoot} from 'react-dom/client'

export default function Homepage({ languageOptions, imageTypeOptions, errorLogger, databaseEndpoints }) {
    console.log("Homepage.RERENDER Homepage language options:", languageOptions);
    const [selectedFile, setSelectedFile] = useState(null);
    const [allPages, setAllPages] = useState({});
    const [pageNumber, setPageNumber] = useState(0);
    const [selectedLanguage, setSelectedLanguage] = useState("");
    const [selectedImageType, setSelectedImageType] = useState("");
    const [selectedSecondLanguage, setSelectedSecondLanguage] = useState("");
    const [ocrBoxScale, setOcrBoxScale] = useState(0);
    const [ocrDensityScale, setOcrDensityScale] = useState(0);
    const [ocrConfidenceThreshold, setOcrConfidenceThreshold] = useState(0);
    const [dataToExport, setDataToExport] = useState(false);
    const [documentHash, setDocumentHash] = useState("");
    const [showLoadModal, setShowLoadModal] = useState(false);
    const [tempLoadedData, setTempLoadedData] = useState({});
    const [pdfWidth, setPdfWidth] = useState(0);
    const [pdfHeight, setPdfHeight] = useState(0);
    
    console.log("Homepage: selected Type", selectedImageType);
    // doc: document.querySelector('.react-pdf__Document')
/*
    useEffect(() => {
        const handlePageRendered = () => {
            console.log('Page ${pageNumber} was rendered');
            document.dispatchEvent(new Event('pageRendered'));
        };
        document.addEventListener('pageRendered', handlePageRendered);
        return () => {
            document.removeEventListener('pageRendered', handlePageRendered);
        };

    }, [pageNumber]);
*/



    const exportTables = () => {
        const page = allPages[pageNumber]
        console.log("Homepage.exportTables current Getting page:", page, "index: ", pageNumber)
        const queryText = `[data-page-number='${pageNumber}']`
        console.log("Homepage.exportTables current page", pageNumber ,"Querying for:", queryText)
        const foundElement = document.querySelector(queryText)
        console.log("Homepage.exportTables current page found", foundElement, typeof foundElement)
        const pageBase64 = foundElement.children[0].toDataURL("image/png").split(';base64,')[1]
        console.log("Homepage.exportTables base64", pageBase64, typeof pageBase64)
        console.log("Homepage.exportTables pdf width and height",pdfWidth, pdfHeight)
     
        const inputImageData = { 
            b64data: pageBase64, //"b64 data", // send document or image info, ideally in b64
            internal_id: selectedFile.name+pageNumber, 
        };
    
        axios.post('http://localhost:8088/generate-excel', inputImageData, {
            responseType: 'blob' // Ensure response is treated as a blob
        })
        .then(response => {
            // Create a new Blob object using the response data
            const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = selectedFile.name+"."+pageNumber+".tables.xlsx"; // Use a default name or ensure selectedFile is defined  selectedFile.name+
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(error => {
            console.error('Error:', error);
        });
    };
            
    // Helper function to split text into lines that fit within the box width 
    function splitTextToFit(pdf, text, maxWidth) { 
        const words = text.split(" "); 
        const lines = []; 
        let currentLine = ""; 
    
        words.forEach((word) => { 
            const testLine = currentLine ? `${currentLine} ${word}` : word; 
            const testWidth = pdf.getTextWidth(testLine); 
    
            if (testWidth <= maxWidth) { 
                currentLine = testLine; 
            } else { 
                lines.push(currentLine); 
                currentLine = word; 
            } 
        }); 
    
        if (currentLine) { 
            lines.push(currentLine); 
        } 
        return lines; 
    } 

    // Helper function to calculate font size that fits within the box height 
    function calculateFontSize(pdf, lines, maxHeight) { 
        let fontSize = 18; // Start with the default font size 
        let lineHeight = fontSize + 2; // Approximate line height 
        while (lineHeight * lines.length > maxHeight && fontSize > 1) { 
            fontSize -= 1; // Decrease font size 
            lineHeight = fontSize + 2; // Recalculate line height 
        } 
        return fontSize; 
    } 

    // Helper function to calculate font size that fits within the box height 
    function calculatePNGFontSize(context, lines, maxHeight) { 
        let fontSize = 18; // Start with the default font size 
        let lineHeight = fontSize + 2; // Approximate line height 
        while (lineHeight * lines.length > maxHeight && fontSize > 1) { 
            fontSize -= 1; // Decrease font size 
            lineHeight = fontSize + 2; // Recalculate line height 
        } 
        return fontSize;
        } 
                
        // Helper function to split text into lines that fit within the box width 
        function splitPNGTextToFit(context, text, maxWidth) {
        const words = text.split(" ");
        const lines = []; 
        let currentLine = "";
        words.forEach((word) => { 
            const testLine = currentLine ? `${currentLine} ${word}` : word; 
            const testWidth = context.measureText(testLine).width; 
            if (testWidth <= maxWidth) { 
            currentLine = testLine;
            } else {
            lines.push(currentLine); 
            currentLine = word; 
            } 
        }); 
        if (currentLine) { 
            lines.push(currentLine); 
        } 
        return lines; 
        } 

    const generatePDF = async (pdf, i_page, lastPage, boxesOnly) =>{ 
        
        const previousCanvasElement = document.querySelector('.react-pdf__Page__canvas') ? document.querySelector('.react-pdf__Page__canvas') : document.querySelector(`page_${i_page}`);
        // const previousCanvasElement = await waitForCanvasElement(i_page, lastCanvasElement); // wait for the image to re-render
        // lastCanvasElement = previousCanvasElement;

        const pageImageData = previousCanvasElement.toDataURL("image/png"); 
        pdf.addImage(pageImageData, "PNG", 0, 0, pdfWidth, pdfHeight); 
        const pageData = allPages[i_page]; 

        pageData.boxes.forEach((box, boxIndex) => { 
            const x = box.x * pdfWidth; 
            const y = box.y * pdfHeight; 
            const w = box.w * pdfWidth; 
            const h = box.h * pdfHeight; 
            
            pdf.setDrawColor(0, 0, 255); // Blue color 
            pdf.setLineWidth(1);     
            pdf.rect(x, y, w, h); 
            pdf.setTextColor(0, 0, 255); // Blue color 
            pdf.setFont("helvetica", "normal"); 
            pdf.setFontSize(10); 
            pdf.text(`${i_page}.${boxIndex}`, x + w + 3, y + h); 
            
            if (box.translation && !boxesOnly) { 
                // Draw the white background
                pdf.setFillColor(255,255,255);
                pdf.rect(x,y,w,h, "F")
                pdf.setTextColor(0, 0, 0);
                pdf.setFont("helvetica", "normal"); 
                const defaultFontSize = 20; 
                pdf.setFontSize(defaultFontSize); 
                const lines = splitTextToFit(pdf, box.translation, w - 4); 
                const lineHeight = defaultFontSize + 2; 
                const totalHeight = lines.length * lineHeight; 
                let fontSize = defaultFontSize; 
                if (totalHeight > h - 4) { 
                    fontSize = calculateFontSize(pdf, lines, h - 4); 
                } 
                pdf.setFontSize(fontSize); 
                let textY = y + 20; 
                lines.forEach((line) => { 
                    pdf.text(line, x + 2, textY); 
                    textY += fontSize + 2;
                }); 
            } 
        });

        if(lastPage === false){
            pdf.addPage([pdfWidth, pdfHeight]); 
        }
        else {
            const filename = `${selectedFile.name.split(".")[0]}_overlay.pdf`; 
            pdf.save(filename); 
        }
    }

    function generatePNG(i_page, boxesOnly) { 
        console.log("current allpages", allPages); 
        console.log("Current SelectedFile", selectedFile); 
        const filename = `${selectedFile.name}.${i_page}.overlay.png`; 
        const previousCanvasElement = document.querySelector('.react-pdf__Page__canvas') ? document.querySelector('.react-pdf__Page__canvas') : document.querySelector(`page_${pageNumber}`);
        const newCanvasElement = document.createElement('canvas'); 
        newCanvasElement.width = previousCanvasElement.width; 
        newCanvasElement.height = previousCanvasElement.height; 
        const context = newCanvasElement.getContext("2d", { desynchronized: false }); 
        context.drawImage(previousCanvasElement, 0, 0); 
        allPages[i_page].boxes.forEach(function (box, boxIndex) { 
            const x = box.x * pdfWidth; 
            const y = box.y * pdfHeight; 
            const w = box.w * pdfWidth; 
            const h = box.h * pdfHeight; 

            context.scale(1, 1); 
            context.lineWidth = 1; 
            context.strokeStyle = "blue"; 
            context.font = "small-caps 100 .65rem serif"; 
            context.strokeRect(box.x * pdfWidth, box.y * pdfHeight, box.w * pdfWidth, box.h * pdfHeight); 
            context.strokeText(`${i_page}.${boxIndex}`, ((box.x + box.w) * pdfWidth) + 3, (box.y + box.h) * pdfHeight); 

            if (box.translation && !boxesOnly) { 
                // Draw the white background 
                context.fillStyle = "white"; 
                context.fillRect(x, y, w, h); 
                context.fillStyle = "black"; 
                const defaultFontSize = 20; 
                context.font = `${defaultFontSize}px Helvetica`; 
                const lines = splitPNGTextToFit(context, box.translation, w - 4); 
                const lineHeight = defaultFontSize + 2; 
                const totalHeight = lines.length * lineHeight; 
                let fontSize = defaultFontSize; 
                if (totalHeight > h - 4) { 
                  fontSize = calculatePNGFontSize(context, lines, h - 4); 
                } 
    
                context.font = `${fontSize}px Helvetica`; 
                let textY = y + 20; 
              
                lines.forEach((line) => { 
                  context.fillText(line, x + 2, textY); 
                  textY += fontSize + 2; 
                }); 
              } 
        }); 
        downloadPicture(newCanvasElement.toDataURL("image/png"), filename); 
        console.log("Current pageNumber", pageNumber); 
        console.log("Current pageNumber(i_page)", i_page); 
    } 

    const waitForPageRender = (pageNum) => { 
        return new Promise((resolve) => { 
          const queryText = `[data-page-number='${pageNum}']`;
          const foundElement = document.querySelector(queryText);
          if (foundElement) { 
            console.log(`Page ${pageNum} is already rendered`); 
            resolve(); // Resolve immediately if the page is already rendered 
          } else {
            const listener = () => { 
              resolve(); 
              document.removeEventListener('pageRendered', listener); 
            }; 
            document.addEventListener('pageRendered', listener); 
          } 
        }); 
    }; 



    const export_multiple = async (times, format, boxesOnly) => { 
        const pdf = format === "pdf" ? new jsPDF({ orientation: "portrait", unit: "px", format: [pdfWidth, pdfHeight] }) : null; // Only create a PDF instance if the format is "pdf" 

        //code using useEffect promise instead of timeouts
        for (let i=1; i<=times; i++){
            setPageNumber(i);
            await waitForPageRender(i); // Wait for the page to render 
            /* //alternate way with listener events. This doesn't handle exporting from the first page
            await new Promise((resolve) => {
                const listener = () => {
                    resolve();
                    document.removeEventListener('pageRendered',listener);
                };
                document.addEventListener('pageRendered',listener);
            });*/
        
            if (format === "image"){
                generatePNG(i, boxesOnly);
            }
            else if (format === "pdf"){
                generatePDF(pdf, i, i===times, boxesOnly);
            }
        }
    };


    function generateOverlayPicture(exportAllPages, exportPDF, boxesOnly) { 
        var format = exportPDF ? "pdf": "image";

        if (!selectedFile || !Object.keys(allPages).length) {    
            console.error("No file or pages available to generate overlays.");    
            return;    
        } 
        if (exportAllPages) { 
            if(pageNumber ===1){
                document.dispatchEvent(new Event('pageRendered'));
            }
            export_multiple(Object.keys(allPages).length, format, boxesOnly); 
        } 
        else { 
            if (format === "image") { 
                generatePNG(pageNumber, boxesOnly);
            } 
            else if (format === "pdf") { 
                const pdf = new jsPDF({     //create new jsPDF instance 
                    orientation: "portrait", 
                    unit: "px", 
                    format: [pdfWidth, pdfHeight], 
                }); 
                generatePDF(pdf, pageNumber, true, boxesOnly); // Generate a single-page PDF 
            } 
        } 
    } 

/*
    // orginal function
    function generateOverlayPicture(exportAllPages) {
        if(!exportAllPages){
            const filename = `${selectedFile.name}.${pageNumber}.overlay.png`
            const previousCanvasElement = document.querySelector('.react-pdf__Page__canvas') ? document.querySelector('.react-pdf__Page__canvas') : document.querySelector(`page_${pageNumber}`);
            const newCanvasElement = document.createElement('canvas');
            newCanvasElement.width = previousCanvasElement.width;
            newCanvasElement.height = previousCanvasElement.height;
            const context = newCanvasElement.getContext("2d", { desynchronized: false });
            context.drawImage(previousCanvasElement, 0, 0);
            allPages[pageNumber].boxes.forEach(function (box, boxIndex) {
                context.scale(1, 1);
                context.lineWidth = 1;
                context.strokeStyle = "blue";
                context.font = "small-caps 100 .65rem serif";
                context.strokeRect(box.x*pdfWidth, box.y*pdfHeight, box.w*pdfWidth, box.h*pdfHeight);
                context.strokeText(`${pageNumber}.${boxIndex}`, ((box.x+box.w)*pdfWidth)+3, (box.y+box.h)*pdfHeight);
            })
            downloadPicture(newCanvasElement.toDataURL("image/png"), filename);  
        }
        else{
            var ii = 0;
            for (const index1 in allPages){
                ii+=1;
            }
            console.log("Exporting", ii, "Overlay Pages")
            export_multiple(ii);
        }
    }    
*/


    function loadTempData() {
        console.log("Homepage.loadTempData Confirmed they want the data", tempLoadedData);
        setAllPages({...tempLoadedData});
        setDataToExport(true);
        setTempLoadedData({})
    }
    function discardTempData() {
        console.log("Homepage.Confirmed they DO NOT want the data");
        apiDiscardData();
        // alert('not currently discarding data, see console for temp data');
        setTempLoadedData({})
    }
    function parseJsonState(sessionData) {
        console.log("Homepage.parseJsonState", sessionData);
        const parsedState = {};
        sessionData.forEach((pageStr) => {
            const page = JSON.parse(pageStr)
            console.log("Homepage.parseJsonState page:", page.page_name, "number:", page.page_number);
            parsedState[page.page_number] = {
                boxes: page.boxes,
                name: page.page_name
            }
        })
        console.log("Homepage.parseJsonState final state:", parsedState);
        return parsedState;
    }

    function apiCheckLoadData(docStr) {
        // send the following to the api: {src_hash: docStr}
        // if found then you get {Session: [{ObjectID, Page Number, Boxes, Page Name, Translation}]}
        console.log("Homepage.apiCheckLoadData request:", docStr)
        let test = languageOptions.filter((lang) => lang.value === 'english')[0]
        console.log("Homepage.apiCheckLoadData test:", test)
        const backend = languageOptions.filter((lang) => lang.value === 'english')[0].backend
        console.log("Homepage.apiCheckLoadData backend:", backend)
        const loadRequestData = { src_hash: docStr }
        console.log("Homepage.apiCheckLoadData loadRequestData:", loadRequestData)

        const data = axios.post(backend + databaseEndpoints.loadSession, loadRequestData).then((response) => {
            console.log(`Homepage.apiCheckLoadData response ${response.status}:`, response.data);
            if (response.data.Session && response.data.Session === "No matching records exist.") {
                console.log(`Homepage.apiCheckLoadData API no data to load for ${docStr}: ${response.data.Session}`);
            } else if (response.data.Session){
                console.log("Homepage.apiCheckLoadData got something for this document: ", response.data.Session)
                const newAllPageData = parseJsonState(response.data.Session);
                console.log("Homepage.apiCheckLoadData newAllPageData: ", newAllPageData);
                setTempLoadedData(newAllPageData);
                setShowLoadModal(true);
            }
            console.log("Homepage.apiCheckLoadData finished");

            return Promise.resolve();
        }).catch(function (error) {
            console.error(error);
            errorLogger(`apiCheckLoadData API Bad response: ${error instanceof Object ? JSON.stringify(error) : error}`);
            return Promise.reject();
        });
    }

    function apiDiscardData() {
        // send the following to the api: {src_hash: ""}
        // if return['Deleted'] == True then good, otherwise error
        const backend = languageOptions.filter((lang) => lang.value === 'english')[0].backend
        const discardRequestData = {
            src_hash: documentHash
        }
        const data = axios.post(backend + databaseEndpoints.discardSession, discardRequestData).then((response) => {
            console.log(`Homepage.apiDiscardData response ${response.status}:`, response.data);
            if (response.data.Deleted && response.data.Deleted === true) {
                console.log("Homepage.apiDiscardData deleted: ", response.data.Deleted)
                // setTempLoadedData({});
            } else {
                errorLogger(`apiDiscardData API error response: ${response.data}`);
            }
            return Promise.resolve();
        }).catch(function (error) {
            console.error(error);
            errorLogger(`apiDiscardData API Bad response: ${error instanceof Object ? JSON.stringify(error) : error}`);
            return Promise.reject();
        });
    }
    
    function apiSaveData() {
        // send the following to the api: {page_state: {hash: "", allPages: allPages}}
        // if 'Session_IDs' in return then good, otherwise error
        const languageOption = languageOptions.filter((lang) => lang.value === 'english')[0];
        const saveRequestData = {
            hash: documentHash,
            allPages: Object.fromEntries(
                Object.entries(allPages).map(([pNum, pData]) => {
                    return [
                        pNum, {
                            ...pData,
                            boxes: pData.boxes.map((box) => {
                                return {
                                    ...box,
                                    x: box.x,
                                    y: box.y,   
                                    w: box.w,
                                    h: box.h
                                }
                                
                            }).filter(box => {console.log("Homepage.apiSaveData Box:", box, "text" in box && "translation" in box && "type" in box); return ("text" in box && "translation" in box && "type" in box)})
                        } 
                    ]
                })
            )
        }
        console.log(`Homepage.apiSaveData request:`, saveRequestData);

        const data = axios.post(languageOption.backend + databaseEndpoints.saveSession, saveRequestData).then((response) => {
            console.log(`Homepage.apiSaveData response ${response.status}:`, response.data);
            if (response.data.Session_IDs) {
                if (response.data.Session_IDs.toString().includes('already exists')) {
                    alert("This state has already been saved!")
                } else {
                    alert("Saved!");
                }
                console.log("Homepage.apiSaveData session ids: " + response.data.Session_IDs.toString());
            } else {
                errorLogger(`apiSaveData API error response: ${response.data}`);
            }
            return Promise.resolve();
        }).catch(function (error) {
            console.error(error);
            errorLogger(`apiSaveData API Bad response: ${error instanceof Object ? JSON.stringify(error) : error}`);
            return Promise.reject();
        });
    }
    function getPageData(page) {
        console.log("Homepage.getPageData Getting page:", page)
        return {
            name: page.name,
            boxes: page.data.map(function(data) {
                setDataToExport(true);
                return {
                    x: data.bounding_box.at(0) / pdfWidth,
                    y: data.bounding_box.at(1) / pdfHeight,
                    w: data.bounding_box.at(2) / pdfWidth,
                    h: data.bounding_box.at(3) / pdfHeight,
                    text: data.text,
                    translation: data.translation,
                    type: selectedImageType,
                }
            })
        }
    }


    function handleReturnDataStage1(data) {
        console.log("Homepage.handleReturnDataStage1: allpages was", allPages);
        console.log("Homepage.handleReturnDataStage1: data", data, typeof data);
        if (data) {
            const newAllPages = {}
            console.log('Homepage.handleReturnDataStage1: found data')
            for (const page of data){
                console.log("Homepage.handleReturnDataStage1: page", page);
                const thisPageDataNumber = page.name.match(/([a-z]$)/gi) ? page.name.split(".").at(-2) : page.name.split(".").at(-1)
                console.log("Homepage.handleReturnDataStage1: number", thisPageDataNumber);
                newAllPages[thisPageDataNumber] = getPageData(page);
                console.log("Homepage.handleReturnDataStage1: pdf width and height:", pdfWidth, pdfHeight)
            }
            
            console.log("Homepage.handleReturnDataStage1 setting all page data via newpages:", newAllPages)
    
            setAllPages(allPages => ({
                ...allPages,
                ...newAllPages
            }))
        } else {
            errorLogger(`No Script Boxes returned ${data}`)
        }
    }

    function handleReturnDataStage2(data) {
        console.log("Homepage.handleReturnDataStage2: allpages was", allPages);
        console.log("Homepage.handleReturnDataStage2: data", data, typeof data);
        if (data) {
            const pageToBoxesMapping = {...allPages}
            for (const [translationId, translatedText] of Object.entries(data)){
                console.log("Homepage.handleReturnDataStage2 Getting id:", translationId, "translation:", translatedText)
                const thisPageDataNumber = translationId.split(".")[0]
                const thisBoxNumber = parseInt(translationId.split(".")[1])
                const currentPageData = allPages[thisPageDataNumber]
                const thisBoxData = currentPageData.boxes.at(thisBoxNumber)
                console.log("Homepage.handleReturnDataStage2 number:", thisPageDataNumber, "box:", thisBoxNumber)
                console.log("Homepage.handleReturnDataStage2 current page data:", currentPageData, "box:", thisBoxData)
                pageToBoxesMapping[thisPageDataNumber].boxes[thisBoxNumber] = {...thisBoxData, translation: translatedText}
                console.log("Homepage.handleReturnDataStage2 new data:", pageToBoxesMapping[thisPageDataNumber].boxes[thisBoxNumber])
            }
            console.log("Homepage.handleReturnDataStage2 setting all page data via newpages:", pageToBoxesMapping)
            setAllPages(pageToBoxesMapping)
        } else {
            errorLogger("No Translations returned")
        }
    }

    async function gatherStage1Data(sendAllPages) {
        const allRequestData = []
        console.log("Homepage.gatherStage1Data:", allPages, typeof allPages)

        if (sendAllPages) {
            alert("Performing OCR on all Pages. This may take a moment.");
            console.log("Homepage.gatherStage1Data ALL", sendAllPages)
            for (const index in allPages){
                setPageNumber(parseInt(index));
                await waitForPageRender(parseInt(index)); // Wait for the page to render 
                const page = allPages[index]

                console.log("Homepage.gatherStage1Data Getting current page:", page, "index: ", index)
               // const queryText = '.react-pdf__Page__canvas'

                const queryText = `[data-page-number='${index}']`
                console.log("Homepage.gatherStage1Data current page", index ,"Querying for:", queryText)
                const foundElement = document.querySelector(queryText)

                if (!foundElement) { 
                    console.error(`Homepage.gatherStage1Data: Page ${index} not found.`); 
                    continue; 
                } 

                console.log("Homepage.gatherStage1Data current page found", foundElement, typeof foundElement)
                const pageBase64 = foundElement.children[0].toDataURL("image/png").split(';base64,')[1]
                console.log("Homepage.gatherStage1Data base64", pageBase64, typeof pageBase64)
                console.log("Homepage.gatherStage1Data pdf width and height",pdfWidth, pdfHeight)
                const pageData = {
                    name: page.name,
                    b64data: pageBase64,
                    src_lang: selectedLanguage,
                    image_type: selectedImageType,
                    box_scale: ocrBoxScale,
                    density_scale: ocrDensityScale,
                    conf_threshold: ocrConfidenceThreshold,
                    boxes: page.boxes.length > 0 ? page.boxes.filter((box) => box.h > 0 && box.w > 0).map(function (boxData) {return [Math.round(boxData.x * pdfWidth), Math.round(boxData.y * pdfHeight), Math.round(boxData.w * pdfWidth), Math.round(boxData.h * pdfHeight)]}): []
                }
                console.debug("Homepage.gatherStage1Data requestdata for page ", pageData)
                allRequestData.push(pageData)
            }
        
        } else {
            const page = allPages[pageNumber]
            console.log("Homepage.gatherStage1Data specific Getting page:", page, "Number:", pageNumber)
            // const queryText = `[data-page-number='${pageNumber}']`
            const queryText = '.react-pdf__Page__canvas'
            console.log("Homepage.gatherStage1Data specific page", pageNumber ,"Querying for:", queryText)
            const foundElement = document.querySelector(queryText)
            console.log("Homepage.gatherStage1Data specific page found", foundElement, typeof foundElement)
            const pageBase64 = foundElement.toDataURL("image/png", 1.0).split(';base64,')[1]
            console.log("Homepage.gatherStage1Data specific pdf width and height",pdfWidth, pdfHeight)

            const pageData = {
                name: selectedFile.name.split(".").slice(0, -1).toString().concat(`.${pageNumber}`),
                b64data: pageBase64,
                src_lang: selectedLanguage,
                image_type: selectedImageType,
                box_scale: ocrBoxScale,
                density_scale: ocrDensityScale,
                conf_threshold: ocrConfidenceThreshold,
                boxes: page.boxes.length > 0 ? page.boxes.filter((box) => box.h > 0 && box.w > 0).map(function (boxData) {return [Math.round(boxData.x * pdfWidth), Math.round(boxData.y * pdfHeight), Math.round(boxData.w * pdfWidth), Math.round(boxData.h * pdfHeight)]}) : []
            }
            console.debug("Homepage.gatherStage1Data specific requestdata for page ", pageData)

            allRequestData.push(pageData)
    
        }
        console.debug("Homepage.gatherStage1Data all request data ", allRequestData)

        return allRequestData;
    }
    //const gatherStage2Data = async(sendAllPages) =>{
    async function gatherStage2Data(sendAllPages) {
        const allRequestData = {"translations": []}
        console.log("Homepage.gatherStage2Data:", allPages, typeof allPages)
        if (sendAllPages) {
            alert("Performing Translation on all Pages. This may take a moment.");
            console.log("Homepage.gatherStage2Data ALL", sendAllPages)
            for (const pageIndex in allPages) {
                // setPageNumber(parseInt(pageIndex));
                // await waitForPageRender(parseInt(pageIndex)); // don't need to re-render if the OCR data is already saved for each page

                const page = allPages[pageIndex]
                console.log("Homepage.gatherStage2Data current getting page:", page, "index: ", pageIndex)
                page.boxes.forEach(function (box, boxIndex) {
                    console.log("Homepage.gatherStage2Data current box:", box, "index:", boxIndex)
                    if (box.text){
                        allRequestData['translations'].push({
                            text: box.text,
                            src_lang: selectedLanguage,
                            dst_lang: selectedSecondLanguage,
                            id: `${pageIndex}.${boxIndex}`
                        })
                        console.debug("Homepage.gatherStage2Data requestdata for box:", allRequestData['translations'].at(-1))
                    }
                });
            }
        
        } else {
            console.log("Homepage.gatherStage2Data page:", pageNumber)

            const page = allPages[pageNumber]
            console.log("Homepage.gatherStage2Data specific current getting page:", page, "index: ", pageNumber)
            page.boxes.forEach(function (box, boxIndex) {
                console.log("Homepage.gatherStage2Data current box:", box, "index:", boxIndex)
                if (box.text){
                    allRequestData['translations'].push({
                        text: box.text,
                        src_lang: selectedLanguage,
                        dst_lang: selectedSecondLanguage,
                        id: `${pageNumber}.${boxIndex}`
                    })
                    console.debug("Homepage.gatherStage2Data specific requestdata for box:", allRequestData['translations'].at(-1))
                }
            });
    
        }
        console.debug("Homepage.gatherStage2Data all request data ", allRequestData)
        return allRequestData
    }
                    
    const exportModal = <ExportModal exportDisabled={!selectedFile || !dataToExport} selectedFile={selectedFile} pageNumber={pageNumber} allPages={allPages} />;
    const documentHashTooltip = <Tooltip>{documentHash}</Tooltip>

    return (
        <>
            <MenuBar exportDisabled={!selectedFile || !dataToExport} exportModal={exportModal} apiSaveData={apiSaveData} generateOverlayPicture={generateOverlayPicture} exportTables={exportTables} selectedImageType={selectedImageType}/>
            <Container fluid style={{minHeight: '100vh'}}>
                <Row id='rootHomepageRow' style={{minHeight: '100vh'}}>
                    <Col lg="8">
                        <Row>
                            {/* <h3>Stage: {selectedFile && selectedFile.name ? selectedFile.name : 'Document' }</h3> */}
                            {documentHash ?
                                <OverlayTrigger placement='bottom-start' overlay={documentHashTooltip}>
                                    <h3 style={{textDecorationLine: 'underline', color: 'blue'}}>
                                        Stage: Document
                                    </h3>
                                </OverlayTrigger>
                                :<h3> Stage: Document</h3>
                            }
                        </Row>
                        <Row>
                            <Accordion defaultActiveKey={['0']} alwaysOpen>
                                <Accordion.Item eventKey='0'>
                                    <Accordion.Header>Options</Accordion.Header>
                                    <Accordion.Body >

                                        <div style={{marginTop: '.5em', marginBottom: '.5em'}}>
                                            <SelectFileButton selectedFile={selectedFile} setSelectedFile={setSelectedFile} setDocumentHash={setDocumentHash} setAllPages={setAllPages} apiCheckLoadData={apiCheckLoadData} errorLogger={errorLogger} />
                                        </div>
                                        <div style={{marginTop: '.5em', marginBottom: '.5em'}}>
                                            <LanguageDropdown languageOptions={languageOptions} setSelectedLanguage={setSelectedLanguage} />
                                        </div>
                                        <div style={{marginTop: '.5em', marginBottom: '.5em'}}>
                                            <ImageTypeDropdown setSelectedImageType={setSelectedImageType} imageTypeOptions={imageTypeOptions} />
                                        </div>
                                        <div className='text-end'>
                                            <OCRButton callback={handleReturnDataStage1} gatherStage1Data={gatherStage1Data} languageOptions={languageOptions} selectedLanguage={selectedLanguage} readyTriggers={selectedLanguage && selectedFile && selectedFile.name && selectedImageType && allPages} errorLogger={errorLogger} />
                                        </div>
                                    </Accordion.Body>
                                </Accordion.Item>
            
                                <Accordion.Item eventKey='1'>
                                    <Accordion.Header>Advanced Options</Accordion.Header>
                                    <Accordion.Body>
                                        <Col>
                                            <Scale scaleName="Box Scale" scaleValue={ocrBoxScale} setScaleValue={setOcrBoxScale} maxValue={20} scaleTipText={"Determines how large the boxes that get drawn will likely be"} />
                                        </Col>
                                        <Col>
                                            <Scale scaleName="Density Scale" scaleValue={ocrDensityScale} setScaleValue={setOcrDensityScale} maxValue={20} scaleTipText={"Determines the density of the boxes that get drawn will likely be"}/>
                                        </Col>
                                        <Col>
                                            <Scale scaleName="Confidence Threshold" scaleValue={ocrConfidenceThreshold} setScaleValue={setOcrConfidenceThreshold} maxValue={99} scaleTipText={"Minimum confidence value of the text in found boxes such that we will display it"}/>
                                        </Col>
                                    </Accordion.Body>
                                </Accordion.Item>
                            </Accordion>
                        </Row>
                        {!!selectedFile && <DocumentViewer viewerId={selectedFile.name + "_canvas"} setAllPages={setAllPages} setDataToExport={setDataToExport} allPages={allPages} pageNumber={pageNumber} setPageNumber={setPageNumber} selectedFile={selectedFile} setSelectedFile={setSelectedFile} pdfHeight={pdfHeight} pdfWidth={pdfWidth} setPdfWidth={setPdfWidth} setPdfHeight={setPdfHeight} />}
                        <div id="pdf-container" style={{display: 'none'}}></div>
                    </Col>
                    <Col lg="4">
                        <Row>
                            <h3>Stage: OCR/Translate</h3>
                        </Row>
                        <Row>
                            <Col>
                                <LanguageDropdown languageOptions={languageOptions.filter((opt) => {return opt.label === "English"})} setSelectedLanguage={setSelectedSecondLanguage} />
                            </Col>
                            <Col className='text-end'>
                                <TranslateButton callback={handleReturnDataStage2} triggerDataUpdate={() => updateAllTextFromContent(pageNumber, allPages, setAllPages)} gatherStage2Data={gatherStage2Data} stageName="Translate" languageOptions={languageOptions} selectedLanguage={selectedLanguage} selectedSecondLanguage={selectedSecondLanguage} readyTriggers={selectedSecondLanguage && allPages && pageNumber in allPages && allPages[pageNumber].boxes.length > 0} errorLogger={errorLogger}/>
                            </Col>
                            <Col className='text-end'>
                                <ClearStagesButton setAllPages={setAllPages} setDocumentHash={setDocumentHash} setSelectedFile={setSelectedFile} setDataToExport={setDataToExport}/>
                            </Col>

                        </Row>
                        <Row>
                            <Content allPages={allPages} setAllPages={setAllPages} selectedFile={selectedFile} currentPageNumber={pageNumber} setDataToExport={setDataToExport}/>
                        </Row>
                    </Col>
                </Row>
            </Container>
            <LoadModal showLoadModal={showLoadModal} setShowLoadModal={setShowLoadModal} loadTempData={loadTempData} discardTempData={discardTempData} tempLoadedData={tempLoadedData} documentTitle={selectedFile ? selectedFile.name : ''} />

        </>
    );
}
