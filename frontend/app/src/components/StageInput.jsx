import ListGroup from 'react-bootstrap/ListGroup';
import Form from 'react-bootstrap/Form';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';
import { convertCurrentPageToCSV, convertRowToCSV } from '../utilities/export';

export function updateAllTextFromContent(currentPageNumber, allPages, setAllPages) {
    const newPages = {...allPages}
    let changed = false;
    console.log("StageInput.updateAllTextFromContent New pages before", newPages)
    const page = allPages[currentPageNumber]
    console.log("StageInput.updateAllTextFromContent current getting page:", page, "index: ", currentPageNumber)
    page.boxes.forEach(function (box, boxIndex) {
        console.log("StageInput.updateAllTextFromContent current box:", box, "index:", boxIndex)
        const thisOcrEditableBox = document.querySelector(`#editable_box_${boxIndex}`)
        console.log("StageInput.updateAllTextFromContent editable_box_ :", thisOcrEditableBox);

        if (thisOcrEditableBox && box.text !== thisOcrEditableBox.textContent) {
            console.log(`!!!updateAllTextFromContent box changed from: ${box.text} to ${thisOcrEditableBox.textContent}`)
            box.text = thisOcrEditableBox.textContent
            changed = true;
        }
        console.debug("StageInput.updateAllTextFromContent requestdata for box:", box)
    });
    if (changed) {
        console.log("StageInput.updateAllTextFromContent Changed, new pages after", {...newPages, [currentPageNumber]: page})
        setAllPages({...newPages, [currentPageNumber]: page});
    } else {
        console.log("StageInput.updateAllTextFromContent no changes detected")
    }

}

export function updateAllTranslationFromContent(currentPageNumber, allPages, setAllPages) { 
    const newPages = {...allPages}; 
    let changed = false;
    console.log("StageInput.updateAllTranslationFromContent New pages before", newPages); 
    const page = allPages[currentPageNumber]; 
    console.log("StageInput.updateAllTranslationFromContent current getting page:", page, "index: ", currentPageNumber); 
    page.boxes.forEach(function (box, boxIndex) { 
        console.log("StageInput.updateAllTranslationFromContent current box:", box, "index:", boxIndex); 
        const thisTranslationEditableBox = document.querySelector(`#editable_translation_box_${boxIndex}`); 
        console.log("StageInput.updateAllTranslationFromContent editable_translation_box_ :", thisTranslationEditableBox); 

        if (thisTranslationEditableBox && box.translation !== thisTranslationEditableBox.textContent) { 
            console.log(`!!!updateAllTranslationFromContent box translation changed from: ${box.translation} to ${thisTranslationEditableBox.textContent}`); 
            box.translation = thisTranslationEditableBox.textContent; 
            changed = true; 
        } 
        console.debug("StageInput.updateAllTranslationFromContent requestdata for box:", box); 
    }); 
    if (changed) { 
        console.log("StageInput.updateAllTranslationFromContent Changed, new pages after", {...newPages, [currentPageNumber]: page}); 
        setAllPages({...newPages, [currentPageNumber]: page}); 
    } else { 
        console.log("StageInput.updateAllTranslationFromContent no changes detected"); 
    } 
} 



export function updateCurrentBoxFromEvent(currentPageNumber, boxIndex, allPages, setAllPages, newText) {
    const newPages = {...allPages}
    console.log("StageInput.updateCurrentBoxFromEvent New pages before", newPages)
    console.log("StageInput.updateCurrentBoxFromEvent event text:", newText)
    newPages[currentPageNumber].boxes[boxIndex].text = newText
    console.log("StageInput.updateCurrentBoxFromEvent New pages after", newPages)
    setAllPages(newPages);
}


export function Content({ allPages, setAllPages, currentPageNumber, setDataToExport, selectedFile }) {
    const currentPageData = allPages[currentPageNumber];
    console.log("StageInput.Content:", allPages);
    console.log("StageInput.Content current page data", currentPageData);
    

    function deleteBox(boxIndex) {
        console.log("StageInput.deleteBox: Box Index:", boxIndex);
        const newPages = {...allPages}
        console.log("StageInput.deleteBox New pages before", newPages)

        if (Object.keys(newPages).length === 1 && currentPageData.boxes.length === 1) {
            setDataToExport(false);
        } else {
            setDataToExport(true);
        }

        newPages[currentPageNumber].boxes.splice(boxIndex, 1)

        console.log("StageInput.deleteBox New pages after", newPages)
        
        setAllPages(newPages);

    }
    function handleTextChange(boxData, boxIndex, e) {
        console.log("StageInput.handleTextChange: Box:", boxData, "Index:", boxIndex, "CurrentPage:", currentPageNumber, "All:", allPages);
        if (e.code === "Enter") {
            updateCurrentBoxFromEvent(currentPageNumber, boxIndex, allPages, setAllPages, e.target.textContent)
            setDataToExport(true);
            e.preventDefault()
        } else {
            console.log("StageInput.Handle text change keydown code:", e.code)
        }

    }
    function handleTranslationChange(boxData, boxIndex, e) { 
        console.log("StageInput.handleTranslationChange: Box:", boxData, "Index:", boxIndex, "CurrentPage:", currentPageNumber, "All:", allPages); 
        if (e.code === "Enter") { 
            updateAllTranslationFromContent(currentPageNumber, allPages, setAllPages); 
            setDataToExport(true); 
            e.preventDefault(); 
        } else { 
            console.log("StageInput.Handle translation change keydown code:", e.code); 
        } 
    } 
    function copyCurrentPageToClipboard(event) {
        console.log("StageInput.copyCurrentPageToClipboard event", event)
        let textToCopy = convertCurrentPageToCSV(allPages[currentPageNumber], currentPageNumber, selectedFile);
        navigator.clipboard.writeText(textToCopy);
        
    }
    function copyRowToClipboard(event, boxIndex) {
        console.log("StageInput.copyRowToClipboard event", event)
        let textToCopy = convertRowToCSV(allPages[currentPageNumber], boxIndex, currentPageNumber, selectedFile);
        navigator.clipboard.writeText(textToCopy);
    }
    function canCopy() {
        if (document.queryCommandSupported) {
            return document.queryCommandSupported('copy');
        } else {
            console.log("StageInput.Query Command Supported is not supported, default to no copy functionality");
            return false;
        }
    }
    const deleteTooltip = <Tooltip>Click here to delete this box</Tooltip>
    const copyTooltip = <Tooltip>Click here copy this row as csv to your clipboard</Tooltip>
    const copyAllTooltip = <Tooltip>Click here copy this page as csv to your clipboard</Tooltip>
    return (
        <div className="contentDiv">
            {(currentPageData && currentPageData.boxes.length >= 1 && canCopy()) && 
                <ListGroup style={{padding: '0.05', marginBottom: '0.15em'}} ><OverlayTrigger overlay={copyAllTooltip}><ListGroup.Item action onClick={copyCurrentPageToClipboard}>Copy All To Clipboard</ListGroup.Item></OverlayTrigger></ListGroup>
            }
            {currentPageData === undefined || currentPageData.boxes.length < 1 ? <ListGroup><ListGroup.Item>Empty</ListGroup.Item></ListGroup> : 
                currentPageData.boxes.map(function (boxData, boxIndex) {
                    return (
                        !boxData || boxData.text === undefined ? "" : 
                            <ListGroup key={"ocrTranslateInput_"+boxIndex} horizontal id={"ocrTranslateInput_"+boxIndex} style={{paddingBottom: ".05em"}}>
                                <OverlayTrigger overlay={deleteTooltip}>
                                    <ListGroup.Item action onClick={(e) => {deleteBox(boxIndex)}} style={{width: "12%", paddingLeft: "revert", paddingRight: "revert", marginRight:'0', marginBottom:'0.15em'}} id={"label_"+currentPageData.name+"_"+boxData.x+boxData.y+boxData.w+boxData.h}>
                                        {`${currentPageNumber}.${boxIndex}`}
                                    </ListGroup.Item>
                                </OverlayTrigger>
                                <ListGroup.Item id={`editable_box_${boxIndex}`} style={{width: canCopy() ? "40%" : "44%", marginRight:'0.15em', marginBottom:'0.15em'}} contentEditable suppressContentEditableWarning={true} onKeyDown={(e) => {handleTextChange(boxData, boxIndex, e); console.log("StageInput.handleTextChange triggered")}}>
                                    {`${boxData.text}`}
                                </ListGroup.Item>
                                {/*
                                <ListGroup.Item style={{width: canCopy() ? "40%" : "44%", marginRight:'0.15em', marginBottom:'0.15em', overflowX: boxData.translation ? 'scroll' : 'auto'}} id={"translate_"+currentPageData.name+"_"+boxData.x+boxData.y+boxData.w+boxData.h}>
                                    {`${boxData.translation}`}
                                </ListGroup.Item>
                                */}
                                <ListGroup.Item id={`editable_translation_box_${boxIndex}`} style={{width: canCopy() ? "40%" : "44%", marginRight:'0.15em', marginBottom:'0.15em', overflowX: boxData.translation ? 'scroll' : 'auto'}} contentEditable suppressContentEditableWarning={true} onKeyDown={(e) => {handleTranslationChange(boxData, boxIndex, e); console.log("StageInput.handleTranslationChange triggered")}} > 
                                    {`${boxData.translation}`} 
                                </ListGroup.Item> 

                                {canCopy() && 
                                    <OverlayTrigger overlay={copyTooltip}>
                                        <ListGroup.Item action style={{width: "8%", marginBottom:'0.15em', padding: 'revert'}} onClick={(event) => copyRowToClipboard(event, boxIndex)}>
                                            <img width='15' height='15' src='clipboard3.jpeg' alt='clipboard icon'/>
                                        </ListGroup.Item>
                                    </OverlayTrigger>

                                }
                            </ListGroup>
                    )
                })
            }
            {currentPageData && currentPageData.boxes.length >= 1 && <div style={{marginTop: '1em'}}> 
                <button className="saveEditsButton" onClick={() => { updateAllTextFromContent(currentPageNumber, allPages, setAllPages); updateAllTranslationFromContent(currentPageNumber, allPages, setAllPages); }} > 
                    Save Edits 
                </button> 
            </div>
            } 
        </div>
    )
}


export function LanguageDropdown({ setSelectedLanguage, languageOptions }) {
    if (languageOptions.length === 1) {
        console.debug(`LanguageDropdown Default language selected${languageOptions[0].value}`)
        setSelectedLanguage(languageOptions[0].value);
    }
    return (
        <Form.Select className='languageDropdown' style={{width: "fit-content"}} aria-label="Language select dropdown" onChange={(e) => setSelectedLanguage(e.target.value)}>
            {languageOptions.length !== 1 &&
                <option value="">Select Language</option>
            }
            {languageOptions.map((language) => <option key={language.label} value={language.value}>{language.label}</option>)}
        </Form.Select>
    );
}


export function ImageTypeDropdown({ setSelectedImageType, imageTypeOptions }) {
    return (
        <Form.Select className='imageTypeDropdown' style={{width: "fit-content"}} aria-label="Image Type select dropdown" onChange={(e) =>  setSelectedImageType(e.target.value)}>
            <option value="">Select Image Type</option>
            {imageTypeOptions.map((imageType) => {return imageType.value === '' ? <option disabled key={imageType.label} value={imageType.value}>{imageType.label}</option> : <option key={imageType.label} value={imageType.value}>{imageType.label}</option> })} 
            {/*previously this disabled the 'table' option from being selected as an image type */}
        </Form.Select>
    );
}



export function Scale({scaleName, scaleValue, setScaleValue, maxValue, scaleTipText}) {
    const scaleTooltip = <Tooltip>{scaleTipText}</Tooltip>
    return (
        <div>
            <OverlayTrigger className='scaleTag' placement='right' overlay={scaleTooltip}>
                <Form.Label className={scaleValue > 0 ? 'enabledScale' : 'disabledScale'}>{scaleName}: {scaleValue}</Form.Label>
            </OverlayTrigger>
            <Form.Range name={scaleName} min={0} max={maxValue} step={1} value={scaleValue} onChange={(e) => {setScaleValue(e.target.value)}}/>
        </div>
    )
}