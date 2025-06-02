import { React } from 'react';
import { useState } from 'react';
import Container from 'react-bootstrap/Container';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import Nav from 'react-bootstrap/Nav';
import Modal from 'react-bootstrap/Modal';
// import exportTables from './Homepage';
// import generateOverlayPicture from './DocumentViewer';

import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';

import { OverlayTrigger, Tooltip } from 'react-bootstrap';


export function MenuBar({ exportDisabled, exportModal, apiSaveData, generateOverlayPicture, exportTables, selectedImageType }) {
    const saveStateTooltip = <Tooltip>Send the current state of the document to the database</Tooltip>
    // const exportPDFToolTip = <Tooltip>Generate a PDF with english overlay</Tooltip>
    const exportPicturesToolTip = <Tooltip>Generate an image of the current state of the document overlay</Tooltip>
    // const exportTableTooltip = <Tooltip>Export a csv of all tables on this page in their original language</Tooltip>    
    const [showModal, setShowModal] = useState(false);
    const handleClose = () => setShowModal(false);
    const handleOpen = () => {
        setShowModal(true);
        setExportAllPages(true);
        setexportPDF(true); // true will be for pdfs, false for pngs
        setBoxesOnly(true); // export only boxes or boxes with the translation on top
    };

    const [exportAllPages, setExportAllPages] = useState(true);
    const [exportPDF, setexportPDF] = useState(true);
    const [boxesOnly, setBoxesOnly] = useState(true);

   // const [selectedImageType, setSelectedImageType] = useState("");
   // const [selectedFile, setSelectedFile] = useState(null);
   console.log("MenuBar: Selected Type:", selectedImageType);


    return (
        <Navbar data-bs-theme='dark' className="bg-body-tertiary" style={{ paddingLeft: "1em" }}>
            <Container fluid>
                <Navbar.Brand>
                    <img 
                        alt="logo"
                        src="/hieroglyph.png"
                        width="35"
                        height="35"
                        className='d-inline-block align-top'
                        />
                    {'  '}
                    Hieroglyph
                </Navbar.Brand>
                <Nav className='mr-auto'>
                    <Navbar.Toggle variant='dark' size='md' disabled={exportDisabled} />
                    <Navbar.Collapse>
                        <Nav>
                            <NavDropdown menuVariant='dark' drop='start' title='Export Options'>
                                {exportModal}
                                <OverlayTrigger placement='left' overlay={saveStateTooltip}>
                                    <NavDropdown.Item className='menuBarButton' variant='secondary' disabled={exportDisabled} onClick={apiSaveData}>Save State To Database</NavDropdown.Item>
                                </OverlayTrigger>
                                {/* 
                                <OverlayTrigger placement='left' overlay={exportPDFToolTip} > 
                                    <NavDropdown.Item className='menuBarButton' variant='secondary' disabled={exportDisabled} onClick={generateOverlayPDF}>Generate Overlay PDF</NavDropdown.Item>
                                </OverlayTrigger>
                                */}
                                <OverlayTrigger placement='left' overlay={exportPicturesToolTip}>
                                    <NavDropdown.Item variant='secondary' className='menuBarButton' disabled={exportDisabled} onClick={handleOpen}>Generate Overlay Picture</NavDropdown.Item >
                                </OverlayTrigger>
                                
                                <Modal show={showModal} onHide={handleClose}>
                                    <Modal.Header closeButton>
                                        <Modal.Title>Generate Overlay Picture</Modal.Title>
                                    </Modal.Header>
                                    <Modal.Body>
                                        <Form>
                                            <div style={{paddingTop: ".5em", paddingBottom: ".5em"}}>
                                                <Form.Check inline name='exportPagesGroup' label='Boxes Only' defaultChecked type='radio' onChange={() => setBoxesOnly(true)}></Form.Check>
                                                <Form.Check inline name='exportPagesGroup' label='Boxes with Translation' type='radio' onChange={() => setBoxesOnly(false)}></Form.Check>
                                            </div>
                                        </Form>
                                        <Form>
                                            <div style={{paddingTop: ".5em", paddingBottom: ".5em"}}>
                                                <Form.Check inline name='exportPagesGroup' label='All Pages' defaultChecked type='radio' onChange={() => setExportAllPages(true)}></Form.Check>
                                                <Form.Check inline name='exportPagesGroup' label='Current Page' type='radio' onChange={() => setExportAllPages(false)}></Form.Check>
                                            </div>
                                        </Form>
                                        <Form>
                                            <div style={{paddingTop: ".5em", paddingBottom: ".5em"}}>
                                                <Form.Check inline name='exportPagesGroup' label='Export to PDF' defaultChecked type='radio' onChange={() => setexportPDF(true)}></Form.Check>
                                                <Form.Check inline name='exportPagesGroup' label='Export to PNG Image' type='radio' onChange={() => setexportPDF(false)}></Form.Check>
                                            </div>
                                        </Form>
                                    </Modal.Body>
                                    <Modal.Footer>
                                        <Button variant='secondary' onClick={handleClose}>Cancel</Button>
                                        <Button variant='primary' onClick={() => generateOverlayPicture(exportAllPages, exportPDF, boxesOnly)}>Export</Button>
                                    </Modal.Footer>
                                </Modal>
                                {/* OLD EXPORT FUNCTION
                                {selectedImageType === "table" && (
                                    <OverlayTrigger placement='left' overlay={exportTableTooltip}>
                                        <NavDropdown.Item className='menuBarButton' variant='secondary' disabled={exportDisabled} onClick={exportTables}>Export Original Table</NavDropdown.Item>
                                    </OverlayTrigger>
                                    )}  
                                    */}
                            </NavDropdown>
                        </Nav>
                    </Navbar.Collapse>
                </Nav>
            </Container>
        </Navbar>
    );
}

