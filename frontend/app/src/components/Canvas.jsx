import { useState, useEffect, useRef } from "react";
// https://stackoverflow.com/questions/10214873/make-canvas-as-wide-and-as-high-as-parent
// https://stackoverflow.com/questions/73198755/how-to-draw-a-selection-rectangle-with-drag-and-drop-on-a-html-canvas



function Canvas({ allPages, setAllPages, pageNumber, name, pdfWidth, pdfHeight, deleteBoxFlag, setDataToExport }) {
    console.log("Canvas props:", { allPages, setAllPages, pageNumber, name, pdfWidth, pdfHeight });
    const [origin, setOrigin] = useState(null);
    const canvasRef = useRef();
    // const [currentBox, setCurrentBox] = useState(null);
    // const [render, setRender] = useState(false);
    // const [canvasBoxes, setCanvasBoxes] = useState({});


    function addBox(box) {
        console.log("Canvas.addBox allpages: ", allPages)
        if(allPages && box && box.x && box.y){
            console.log("Canvas.addBox Getting page ",pageNumber, typeof pageNumber)

            const thisPage = allPages[pageNumber]
            if (thisPage){
                if (thisPage.boxes) {
                    console.log("Canvas.Add: No boxes, adding to the end:", box);
                    drawBoxes({
                        ...allPages,
                        [pageNumber]: {...thisPage, boxes: thisPage.boxes.concat(box)}
                    });
                } else {
                    console.log("Canvas.Add: have boxes, ", thisPage.boxes, ", adding:", box);
                    drawBoxes({
                        ...allPages,
                        [pageNumber]: {...thisPage, boxes: [box]}
                    });
                }
                setDataToExport(true);
            } else {
                console.log("Canvas.Add: thispage was nothing", pageNumber)
            }

        } else {
            console.log("Canvas.addBox error with allpages: ", allPages)
            console.log("Canvas.addBox error with box: ", box)

        }

    }
    function updateLastBox(box) {
        console.log("Canvas.updateLastBox Allpages: ", allPages)

        if(allPages){
            console.log("Canvas.updateLastBox Getting page ",pageNumber)

            const thisPage = allPages[pageNumber]
            if (thisPage) {
                if (thisPage.boxes) {
                    drawBoxes({
                        ...allPages,
                        [pageNumber]: {...thisPage, boxes: thisPage.boxes.slice(0, -1).concat(box)}
                    });
                } else {
                    console.log("Canvas.Update: No boxes, adding to the end:", box);
                    drawBoxes({
                        ...allPages,
                        [pageNumber]: {...thisPage, boxes: [box]}
                    });
                }
            }
        }
    }
    function onContextMenu(e) {
        console.log("Canvas.Preventing context menu inside canvas")
        determineBoxDelete(e)
        // e.preventDefault()
    }

    function onMouseDown(e, deleteBoxFlag) {
        console.log("Canvas.onMouseDown Mouse down:", e.nativeEvent.offsetX, e.nativeEvent.offsetY, deleteBoxFlag);
        const rightClick = e.which === 3 || e.button === 2
        if (deleteBoxFlag) {
            console.log("Canvas.onMouseDown Checking for box to delete:", e.nativeEvent.offsetX, e.nativeEvent.offsetY, deleteBoxFlag, e.which);
            determineBoxDelete(e)
        } else if (rightClick) {
            console.log("Canvas.onMouseDown got right click, ignoring for the oncontextmenu handler");
        } else {
            setOrigin({ x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY });
            addBox({ x: (e.nativeEvent.offsetX / pdfWidth), y: (e.nativeEvent.offsetY / pdfHeight), w: 0, h: 0 });
        }
    }

    function onMouseUp(e) {
        console.log("Canvas.onMouseUp:", e.nativeEvent);
        if (e && origin) {
            const localCurrentBox = calculateBox(e);
            console.log("Canvas.onMouseUp Updating last box: ", localCurrentBox);
            if (localCurrentBox.w === 0 && localCurrentBox.h === 0) {
                console.log("Canvas.onMouseUp ignoring 0 box: ", localCurrentBox)
                // deleteBoxByDimenions(localCurrentBox)
                deleteBox(allPages[pageNumber].boxes.length - 1)
            } else {
                updateLastBox(localCurrentBox);
            }
            // drawBoxes();
        }
        setOrigin(null);
        // setCurrentBox(null);
    }
    
    function onMouseMove(e) {
        // console.log("Canvas.Mouse move:", e, origin);
        if (e && origin) {
            const localCurrentBox = calculateBox(e);
            console.log("Canvas.onMouseMove Updating box: ", localCurrentBox);
            updateLastBox(localCurrentBox);
            // drawBoxes();
        }
    }

    
    function deleteBox(boxIndex) {
        console.log("Canvas.deleteBox: Box Index:", boxIndex);
        const newPages = {...allPages};
        console.log("Canvas.deleteBox New pages before", newPages);
        if (Object.keys(newPages).length === 1 && newPages[pageNumber].boxes.length === 1) {
            setDataToExport(false);
        }
        // delete newPages[pageNumber].boxes[boxIndex]
        newPages[pageNumber].boxes.splice(boxIndex, 1)

        console.log("Canvas.deleteBox New pages after", newPages);
        setAllPages(newPages);
    }
    function checkIfPointInBox(pointX, pointY, boxX, boxY, boxW, boxH) {
        console.log("checkIfPointInBox point x,y:", pointX, pointY)
        console.log("checkIfPointInBox box x,y,w,h:", boxX, boxY, boxW, boxH)
        if (boxW < 0 && boxH < 0) {
            console.log("checkIfPointInBox Negative w and h: box x,y,w,h:", boxX, boxY, boxW, boxH)
            return ((pointX <= boxX) && (pointY <= boxY) && (pointX >= boxX+boxW) && (pointY >= boxY+boxH));
        } else if (boxW < 0) {
            console.log("checkIfPointInBox Negative w: box x,y,w,h:", boxX, boxY, boxW, boxH)
            return ((pointX <= boxX) && (pointY >= boxY) && (pointX >= boxX+boxW) && (pointY <= boxY+boxH));
        } else if (boxH < 0) {
            console.log("checkIfPointInBox Negative h: box x,y,w,h:", boxX, boxY, boxW, boxH)
            return ((pointX >= boxX) && (pointY <= boxY) && (pointX <= boxX+boxW) && (pointY >= boxY+boxH));
        } else {
            console.log("checkIfPointInBox box x,y,w,h:", boxX, boxY, boxW, boxH)
            return ((pointX >= boxX) && (pointY >= boxY) && (pointX <= boxX+boxW) && (pointY <= boxY+boxH));
        }
    }
    
    function determineBoxDelete(e) {
        const [eventX, eventY] = [e.nativeEvent.offsetX, e.nativeEvent.offsetY];
        console.log("Canvas.determineBoxDelete:", eventX, eventY);
        if(allPages){
            console.log("Canvas.determineBoxDelete allpages: ", allPages);
            console.log("Canvas.determineBoxDelete Getting page: ", pageNumber);

            const thisPage = allPages[pageNumber];
            if (thisPage) {
                const boxesToDelete = [];
                thisPage.boxes.forEach(function (box, boxIndex) {
                    console.log("Canvas.determineBoxDelete checking box", box, "For point:", eventX, eventY);
                    console.log("Canvas.determineBoxDelete PdfWidth:", pdfWidth ,"and PdfHeight:", pdfHeight);
                    if (checkIfPointInBox(eventX, eventY, box.x*pdfWidth, box.y*pdfHeight, box.w*pdfWidth, box.h*pdfHeight)) {
                        console.log("Canvas.determineBoxDelete found point in event:", eventX, eventY, "box:", box.x*pdfWidth, box.y*pdfHeight, box.w*pdfWidth, box.h*pdfHeight);
                        boxesToDelete.push(boxIndex)
                    }
                })
                if (boxesToDelete.length > 0) {
                    console.log("Canvas.determineBoxDelete deleting the smallest box by area", boxesToDelete)
                    let foundIndex = boxesToDelete.reduce(function (previousMinIndex, currentMinIndex) {
                        let currentMinArea = thisPage.boxes[currentMinIndex].w * thisPage.boxes[currentMinIndex].h;
                        let previousMinArea = thisPage.boxes[previousMinIndex].w * thisPage.boxes[previousMinIndex].h;
                        return currentMinArea < previousMinArea ? currentMinIndex : previousMinIndex;
                    })
                    console.log("Canvas.determineBoxDelete found index", foundIndex, thisPage.boxes[foundIndex]);

                    e.preventDefault();
                    deleteBox(foundIndex);
                } else {
                    console.log("Canvas.determineBoxDelete no boxes to delete")
                }
            } else {
                console.log("Canvas.determineBoxDelete no boxes on this page:", pageNumber);
            }
        } else {
            console.error("Canvas.determineBoxDelete allpages was nothing:", allPages);
        }
    }


    function calculateBox(e) {
        console.log("Canvas.CalculateBox x,y,w,h:", origin.x / pdfWidth, origin.y / pdfHeight, (e.nativeEvent.offsetX - origin.x), (e.nativeEvent.offsetY - origin.y))
        const calculatedBox = {
            x: origin.x / pdfWidth,
            y: origin.y / pdfHeight,
            w: (e.nativeEvent.offsetX - origin.x) / pdfWidth,
            h: (e.nativeEvent.offsetY - origin.y) / pdfHeight
        };
        console.log("Canvas.CalculateBox, new box:", calculatedBox);
        return calculatedBox;
    }


    function drawBoxes(allPageBoxes) {
        console.debug("Canvas.drawBoxes triggered, allpageboxes: ", allPageBoxes);
        if(allPageBoxes){
            console.debug("Canvas.drawBoxes allpages: ", allPages)
            console.debug("Canvas.drawBoxes Getting page ", pageNumber)

            const thisPage = allPageBoxes[pageNumber]
            if (thisPage) {
                let context = canvasRef.current.getContext('2d', { desynchronized: false });
                console.debug("Canvas.drawBoxes Draw Selection Clearing Context: ", context);
                context.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
                if (thisPage.boxes) {
                    thisPage.boxes.forEach(function (box, boxIndex) {
                        console.debug("Canvas.drawBoxes Drawing box:", box, boxIndex);
                        drawSingleBox(box, `${pageNumber}.${boxIndex}`);
                    });
                    
                    if (allPageBoxes === allPages) {
                        console.debug("Canvas.drawBoxes No change to boxes, do not reset them")
                    } else {
                        console.debug("Canvas.drawBoxes Boxes have been changed change to boxes, do not reset them")
                        setAllPages({...allPageBoxes});
                    }
                }
            } else {
                console.debug("Canvas.drawBoxes no boxes on this page:", pageNumber)
            }
        } else {
            console.error("Canvas.drawBoxes allpages was nothing:", allPageBoxes)
        }
    };

    function drawSingleBox(box, id) {
        console.debug("Canvas.drawSingleBox drawing box, id", box, id)
        console.debug("Canvas.drawSingleBox actual box", box.x*pdfWidth, box.y*pdfHeight, box.w*pdfWidth, box.h*pdfHeight);
        let context = canvasRef.current.getContext('2d', { desynchronized: false });
        console.debug("Canvas.drawSingleBox canvas", canvasRef.current);
        console.debug("Canvas.drawSingleBox width and height", pdfWidth, pdfHeight);

        context.scale(1, 1);
        context.strokeStyle = "blue";
        context.lineWidth = 1;
        context.font = "small-caps 100 .65rem serif";
        context.strokeRect(box.x*pdfWidth, box.y*pdfHeight, box.w*pdfWidth, box.h*pdfHeight);
        context.strokeText(id, (box.x+box.w)*pdfWidth+3, (box.y+box.h)*pdfHeight);
    }

    useEffect(() => {
        console.log("Canvas.UseEffect Triggered:", canvasRef.current, "pdfWidth:", pdfWidth, "pdfHeight:", pdfHeight);

        if (pdfWidth && pdfHeight) {
            canvasRef.current.width = pdfWidth;
            canvasRef.current.height = pdfHeight;
            canvasRef.current.style.width = pdfWidth+"px";
            canvasRef.current.style.height = pdfHeight+"px";
        }
        
        drawBoxes(allPages);

    }, [allPages, pdfHeight, pdfWidth]); // drawBoxes, 

    return (
        <canvas
            id={name + "_canvas"}
            ref={canvasRef}
            className="drawCanvas"
            onMouseDown={(e) => {onMouseDown(e, deleteBoxFlag)}}
            onMouseUp={onMouseUp}
            onMouseMove={onMouseMove}
            onContextMenu={onContextMenu}
            />
    )
}


export { Canvas };
