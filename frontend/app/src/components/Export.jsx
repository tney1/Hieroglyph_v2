import { useState } from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import NavDropdown from 'react-bootstrap/NavDropdown';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

import { exportFunction } from '../utilities/export';

export function ExportModal({ exportDisabled, selectedFile, pageNumber, allPages}) {
    const [showModal, setShowModal] = useState(false);
    const [exportType, setExportType] = useState("csv");
    const [exportAllPages, setExportAllPages] = useState(true);

    const handleClose = () => setShowModal(false);
    const handleOpen = () => {
        setShowModal(true);
        setExportAllPages(true);
    };
    const exportDataTooltip = <Tooltip>Export all current data in CSV, JSON, or Excel Formats</Tooltip>
    
    return (
        <>
            <OverlayTrigger placement='left' overlay={exportDataTooltip}>
                <NavDropdown.Item variant='secondary' className='menuBarButton' disabled={exportDisabled} onClick={handleOpen}>Export Data To File</NavDropdown.Item >
            </OverlayTrigger>
            <Modal show={showModal} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Export Data</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Select style={{paddingTop: ".5em", paddingBottom: ".5em"}} value={exportType} onChange={(e) => setExportType(e.target.value)}>
                            <option value='csv'>CSV</option>
                            {/* <option>Export Type</option> */}
                            { <option value='json'>JSON</option> }
                            { <option value='excel'>Excel (for tables)</option> } 

                        </Form.Select>
                        <div style={{paddingTop: ".5em", paddingBottom: ".5em"}}>
                            <Form.Check inline name='exportPagesGroup' label='All Pages' defaultChecked type='radio' onChange={() => setExportAllPages(true)}></Form.Check>
                            <Form.Check inline name='exportPagesGroup' label='Current Page' type='radio' onChange={() => setExportAllPages(false)}></Form.Check>
                        </div>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant='secondary' onClick={handleClose}>Cancel</Button>
                    <Button variant='primary' disabled={!exportType} onClick={() => exportFunction(exportType, exportAllPages, selectedFile, pageNumber, allPages)}>Export</Button>
                </Modal.Footer>
            </Modal>
        </>
    )
}