import Modal from 'react-bootstrap/Modal';
import ModalDialog from 'react-bootstrap/ModalDialog';
import Button from 'react-bootstrap/Button';

export function LoadModal({ showLoadModal, setShowLoadModal, loadTempData, discardTempData, tempLoadedData, documentTitle }) {
    const handleClose = () => setShowLoadModal(false);
    console.log("LoadModal.Render temp loaded data", tempLoadedData);
    return (
        <>
            <Modal show={showLoadModal} enforceFocus backdrop='static' keyboard={false  } centered onHide={handleClose}>
                <Modal.Header>
                    <Modal.Title>Load Data: {documentTitle}</Modal.Title>
                </Modal.Header>
                <ModalDialog style={{ width: '90%' }}>
                    <textarea readOnly style={{ resize: 'none', overflowY: 'scroll', maxHeight: "80vh", minHeight: "50vh" }} value={JSON.stringify(tempLoadedData, null, ' ')}></textarea> 
                </ModalDialog>
                <Modal.Footer>
                    <Button variant='secondary' onClick={() => {discardTempData(); handleClose()}}>No, Discard Data</Button>
                    <Button variant='primary' onClick={() => {loadTempData(); handleClose()}} >Yes, Load Data</Button>
                </Modal.Footer>
            </Modal>
        </>
    )
}