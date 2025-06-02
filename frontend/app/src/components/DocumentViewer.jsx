import useGlobalEvent from "beautiful-react-hooks/useGlobalEvent";
import { createElement, useRef, useState, useEffect, useCallback } from 'react';
import Button from 'react-bootstrap/Button';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import { Document, Page, pdfjs } from 'react-pdf';
import { Tooltip, OverlayTrigger } from "react-bootstrap";
import { 
    Document as MakeDocument, 
    Page as MakePage, 
    Image as MakeImage, 
    pdf as MakePdf, 
} from '@react-pdf/renderer'
import { Canvas } from './Canvas';
// import { downloadPicture } from '../utilities/export';
// import { OCRButton } from './StageButtons';
// import ReactDOM from 'react-dom'; // Import ReactDOM for rendering

// import { PDFDownloadLink, Document as PDFDocument, Page as PDFPage, Image as PDFImage } from '@react-pdf/renderer';

//import { PDFDocument } from 'pdf-lib';
//import { PDFDocument } from 'pdf-lib/dist/pdf-lib.js'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.js',
    import.meta.url,
).toString();


export default function DocumentViewer({ viewerId, allPages, setAllPages, pageNumber, setPageNumber, setDataToExport, selectedFile, setSelectedFile, pdfHeight, pdfWidth, setPdfWidth, setPdfHeight }) {
    console.debug("DocumentViewer.creation:", selectedFile.name);
    const [numDocumentPages, setNumDocumentPages] = useState(1);
    const [deleteBoxFlag, setDeleteBoxFlag] = useState(false);
    const pageDivRef = useRef();



    const singlePageCallback = useCallback(page => {
        console.debug("DocumentViewer.singlePageCallback change setting width and height from:", pdfWidth, "height:", pdfHeight, page);
        if (page && page.offsetHeight) {
            console.debug("DocumentViewer.singlePageCallback change valid page:", page);
            if (page.width !== page.offsetWidth) {
                console.debug("DocumentViewer.singlePageCallback widths not equal:", page.width, page.offsetWidth);

                page.width = page.offsetWidth;
                page.height = page.offsetHeight;
            }
            setPdfHeight(page.offsetHeight);
            // setPdfWidth(page.offsetWidth);
        } else {
            console.debug("DocumentViewer.singlePageCallback change INVALID page:", page);
        }
    }, []); //pdfWidth, pdfHeight, setPdfHeight]);
    
    const singlePageResize = useCallback(page => {
        console.debug("DocumentViewer.singlePageResize change setting width and height from:", pdfWidth, "height:", pdfHeight);
        if (page && page.offsetHeight && page.offsetWidth) {
            console.debug("DocumentViewer.singlePageResize change valid page width and height:", page.offsetWidth, page.offsetHeight);
            setPdfHeight(page.offsetHeight);
            setPdfWidth(page.offsetWidth);
        } else {
            console.debug("DocumentViewer.singlePageResize change INVALID page:", page);
        }
    }, []); //pdfHeight, pdfWidth, setPdfHeight, setPdfWidth]);

    const onWindowResize = useGlobalEvent("resize");
    onWindowResize((event) => {
        if (selectedFile && selectedFile.isDocument) {
            console.log("DocumentViewer.DOCUMENT resize event:", event)
            singlePageResize(document.querySelector('.react-pdf__Document'))
        }
    });

    function setPageCanvas(page) {
        console.log("DocumentViewer.setPageCanvas: page?", page);
        const pageCanvasObject = document.querySelector('.react-pdf__Page__canvas');
        console.log("DocumentViewer.setPageCanvas: page canvas", pageCanvasObject);
        console.log("DocumentViewer.setPageCanvas: setting width, height to ", pageCanvasObject.width, pageCanvasObject.height);
        pageCanvasObject.style.width = page.width;
        pageCanvasObject.style.height = page.height;

    }

    function handleDocumentLoadSuccess(page) {
        console.log("DocumentViewer.Setting handleDocumentLoadSuccess:", page.numPages, page); 
        setNumDocumentPages(page.numPages);
        setPageNumber(1)

        const docObject = document.querySelector('.react-pdf__Document');
        console.log("DocumentViewer.handleDocumentLoadSuccess: page obj", docObject);
        if (docObject) {
            console.log("DocumentViewer.handleDocumentLoadSuccess: CURRENT", docObject);
            setPdfWidth(docObject.offsetWidth);
            setPdfHeight(docObject.offsetHeight);
        } else {
            console.log("DocumentViewer.handleDocumentLoadSuccess: INVALID CURRENT", docObject); 

        }
        const newPages = {};
        const filename = selectedFile.name.split(".").slice(0, -1).toString();

        for (let pNum = 1; pNum <= page.numPages; pNum++) {
            console.log("DocumentViewer.handleDocumentLoadSuccess pNum:", pNum);
            newPages[pNum] = {
                name: filename.concat(`.${pNum}.png`),
                boxes: []
            }
        }
        setAllPages(newPages);
    }

   
    function goToPage(pageNumber, numPages) {
        console.log("DocumentViewer.goToPage:", pageNumber, " of ", numPages)
        if (pageNumber && pageNumber <= numPages && pageNumber >= 1) {
            console.log("DocumentViewer.goToPage: Setting page number to ", pageNumber)
            setPageNumber(pageNumber);
        } else {
            console.error("DocumentViewer.goToPage: Invalid gotopage number", pageNumber)
        }
    }
    function handleGoToPageEvent(e) {
        const eventNum = parseInt(e.target.value)
        if (eventNum && eventNum <= numDocumentPages && eventNum >= 1) {
            console.info("handleGoToPageEvent new page number", eventNum)
            goToPage(eventNum, numDocumentPages)
        } else if (eventNum > numDocumentPages) {
            console.error("DocumentViewer.handleGoToPageEvent Invalid new page number, too high", eventNum, typeof eventNum)
        } else {
            console.error("DocumentViewer.handleGoToPageEvent Page number allowed to be 0", eventNum, typeof eventNum)
            setPageNumber(0);
        }
    }


    

    function clearAllPageBoxes(){
        let newPages = {}
        let isChanged = false;
        console.log("DocumentViewer.clearAllPageBoxes current allpages:", allPages)

        for (const key in allPages) {
            console.log("DocumentViewer.clearAllPageBoxes key:", key)
            const page = allPages[key]
            console.log("DocumentViewer.clearAllPageBoxes boxes:", page.boxes)
            if (page.boxes.length > 0) {
                console.log("DocumentViewer.clearAllPageBoxes CLEARING")
                isChanged = true
            } else {
                console.log("DocumentViewer.clearAllPageBoxes no boxes to clear")
            }
            newPages[key] = {
                name: page.name,
                boxes: []
            };

        }
        if (isChanged){
            console.log("DocumentViewer.clearAllPageBoxes SETTING ALLPAGES", newPages)
            setAllPages(newPages);
        } else {
            console.log("DocumentViewer.clearAllPageBoxes No changes, ignore clear command")

        }

    }

    function clearCurrentPageBoxes(){
        console.log("DocumentViewer.clearCurrentPageBoxes current allpages:", allPages, typeof allPages)
        let newPage = {}
        let isChanged = false;
        console.log("DocumentViewer.clearCurrentPageBoxes current allpages:", allPages)

        console.log("DocumentViewer.clearCurrentPageBoxes key:", pageNumber)
        const thisPage = allPages[pageNumber]
        console.log("DocumentViewer.clearCurrentPageBoxes thispage:", thisPage)
        if (thisPage){
            console.log("DocumentViewer.clearCurrentPageBoxes boxes:", thisPage.boxes)
            if (thisPage.boxes.length > 0) {
                console.log("DocumentViewer.clearCurrentPageBoxes CLEARING")
                isChanged = true
                newPage = {
                    name: thisPage.name,
                    boxes: []
                };
            } else {
                console.log("DocumentViewer.clearCurrentPageBoxes no boxes to clear")
            }
        }

        if (isChanged){
            console.log("DocumentViewer.clearCurrentPageBoxes SETTING ALLPAGES", allPages, newPage)
            setAllPages(allPages => ({
                ...allPages,
                [pageNumber]: newPage
            }))
        } else {
            console.log("DocumentViewer.clearAllPageBoxes No changes, ignore clear command")

        }

    }

    useEffect(() => {
        console.log("DocumentViewer.useeffect setting width from:", pdfWidth, "height:", pdfHeight);    
        if (selectedFile.isDocument === true) {
            console.log("DocumentViewer.useeffect: IsDocument")
            const newPages = {}
            const filename = selectedFile.name.split(".").slice(0, -1).toString();
            console.log("DocumentViewer.useeffect Creating pages for:", selectedFile.name, " -> ", filename, "Num pages:", numDocumentPages)
            for (let pNum=1; pNum <= numDocumentPages; pNum++) {
                console.log("DocumentViewer.useeffect:", pNum)
                newPages[pNum] = {
                    name: filename.concat(`.${pNum}.png`),
                    boxes: []
                }
            }
            console.log("DocumentViewer.useeffect: All New Pages", newPages)
            setAllPages(newPages)
        // }    
        // } else if (selectedFile.isText === true){
        //     console.log("DocumentViewer.useeffect: IsText")
        //     const newPages = {}
        //     const filename = selectedFile.name.split(".").slice(0, -1).toString();
        //     const numPages = selectedFile.length;
        //     for (let pNum=1; pNum <= numPages; pNum++) {
        //         console.log("DocumentViewer.useeffect:", pNum)
        //         newPages[pNum] = {
        //             name: filename.concat(`.${pNum}.png`),
        //             boxes: [],
        //             content: selectedFile.content[pNum -1],
        //             // try without saving content here 
        //         };
        //     }
        //     console.log("DocumentViewer.useeffect: All New Pages", newPages)
        //     setAllPages(newPages);
        //     setNumDocumentPages(newPages);

        } else {
            console.log("DocumentViewer.useeffect: IsNOTDocument, Render as pdf first:");
            const newPdf = () => {
                console.log("DocumentViewer.useeffect: Creating newPDF from ", selectedFile.content, typeof selectedFile.content);
                return (<MakeDocument>
                    <MakePage size='A4'>
                        <MakeImage src={selectedFile.content}></MakeImage>
                    </MakePage>
                </MakeDocument>)
            }

            console.log("DocumentViewer.useeffect: newpdf:", newPdf);
            if (newPdf) {
                const contentBlob = MakePdf(createElement(newPdf)).toBlob().then((contentBlob) => {
                    console.log("DocumentViewer.useeffect: content blob:", contentBlob);
                    console.log("DocumentViewer.useeffect: setting selectedfile from:", selectedFile);
                    setSelectedFile((prev) => {
                        return {
                            ...prev, 
                            content: contentBlob, 
                            isDocument: true 
                        }
                    });
                    console.log("DocumentViewer.useeffect finished with isNotDocument pages");
                });
       
            } else {
                console.log("DocumentViewer.useeffect: newpdf not valid:", newPdf);
                
            }
        }
    }, [selectedFile]); //, numDocumentPages, pdfHeight, pdfWidth, setAllPages]); 

    const deleteButtonTooltip = <Tooltip>You can also right click inside a box to delete it</Tooltip>

    return (
        <Row id={viewerId}>
            <Col>
                <Row className="aboveDocumentDiv">
                    <Col>
                        {selectedFile.isDocument === true &&
                            <>
                                <div className="float-start">
                                    {<a>Page <Form.Control value={pageNumber} type='text' className="pageNumberField" disabled={!selectedFile.content} onChange={(e) => {handleGoToPageEvent(e)}}></Form.Control> of {(selectedFile.content && numDocumentPages) || "--"}</a>}
                                </div>
                                <Button id="previousPageButton"
                                    variant="secondary"
                                    size="sm"
                                    style={{marginLeft: '3em'}}
                                    className="float-start pageButtons"
                                    onClick={() => { goToPage(pageNumber - 1, numDocumentPages)}}
                                    disabled={!selectedFile.content || (pageNumber <= 1)}
                                >
                                    Previous
                                </Button>
                                <Button id="nextPageButton"
                                    variant="secondary"
                                    size="sm"
                                    className="float-start pageButtons"
                                    onClick={() => { goToPage(pageNumber + 1, numDocumentPages)}}
                                    disabled={!selectedFile.content || (pageNumber >= numDocumentPages)}
                                >
                                    Next
                                </Button>
                            </>
                        }
                    
                    </Col>
                    <Col lg="6">
                        <OverlayTrigger className='viewFileTag' placement='bottom' overlay={deleteButtonTooltip}>
                                <Button className="clearBoxesButton float-end"
                                    onClick={() => setDeleteBoxFlag(!deleteBoxFlag)}
                                    size='sm'
                                    variant={deleteBoxFlag ? 'outline-danger' : 'warning'}
                                >
                                    {deleteBoxFlag ? 'DELETING BOXES' : "Click To Start Deleting Boxes"}
                                </Button>
                            </OverlayTrigger>
                            <Button className="clearBoxesButton float-end"
                                onClick={clearCurrentPageBoxes}
                                size='sm'
                                variant="warning"
                            >
                                Clear Page Boxes
                            </Button>
                            <Button className="clearBoxesButton float-end"
                                onClick={clearAllPageBoxes}
                                size='sm'
                                variant="danger"
                            >
                                Clear ALL Boxes
                            </Button>
                            {/* <Button className="downloadAllButton float-end"
                                onClick={() => callTimes(numDocumentPages)}
                                size='sm'
                                variant="success"
                                >
                                Download All Pages
                             </Button> */}
                    </Col>
                </Row>
                <Row id="documentRow" style={{ padding: 0 }}>
                    {selectedFile.isDocument === true &&
                        <Document
                            file={selectedFile.content}
                            onLoadSuccess={handleDocumentLoadSuccess}
                        >
                            <div key={pageNumber} ref={pageDivRef} className="individualPageDiv">
                                <Page id={`page_${pageNumber}`} canvasRef={singlePageCallback} renderTextLayer={false} renderAnnotationLayer={false} pageNumber={pageNumber} width={pdfWidth} 
                                onRenderSuccess={() => {
                                    const event = new Event('pageRendered');
                                    document.dispatchEvent(event);
                                    console.log('Page $(pageNumber) rendered successfully.');
                                }}/>
                            </div>
                            <Canvas allPages={allPages} pageNumber={pageNumber} setAllPages={setAllPages} setDataToExport={setDataToExport} name={viewerId} pdfWidth={pdfWidth} pdfHeight={pdfHeight} deleteBoxFlag={deleteBoxFlag} />
                        </Document>
                        }
                </Row>
            </Col>
        </Row>
    );

}

