
async function exportToExcel(data) { 
    // Determine the maximum x and y values to scale the grid 
    let maxX = 0; 
    let maxY = 0; 

    let minX = Infinity;
    let minY = Infinity;


    data.boxes.forEach(box => { 
        maxX = Math.max(maxX, box.x + box.w); 
        maxY = Math.max(maxY, box.y + box.h); 

        minX = Math.min(minX, box.x);   
        minY = Math.min(minY, box.y);
    }); 

    data.boxes.forEach(box => {
        box.x -= minX;
        box.y -=minY;
    })
    
    // Introduce a scaling factor for width 
    const widthScalingFactor = 0.5; // Adjust this value as needed (e.g., 0.5 means half the scaling) 
    // Create a new workbook 

    const workbook = new ExcelJS.Workbook(); 
    // Create two sheets: one for text and one for translation 

    const textSheet = workbook.addWorksheet('Text'); 

    const translationSheet = workbook.addWorksheet('Translation'); 

    const textMergedRanges = new Set(); 
    const translationMergedRanges = new Set(); 


    data.boxes.forEach(box => { 

        console.log("TextText: ", box.text, "Translation: ", box.translation);

        // Calculate the starting position of the box in the sheet 
        const startRow = Math.floor((box.y / maxY) * 100) + 1; // ExcelJS rows are 1-based 
        const startCol = Math.floor((box.x / maxX) * 100 * widthScalingFactor) + 1; // ExcelJS columns are 1-based 
        // Calculate the ending position of the box in the sheet 
        const endRow = Math.floor(((box.y + box.h) / maxY) * 100); 
        const endCol = Math.floor(((box.x + box.w) / maxX) * 100 * widthScalingFactor); 

  
        // Place the text and translation in the correct starting cell 
        textSheet.getCell(startRow, startCol).value = box.text; 
        translationSheet.getCell(startRow, startCol).value = box.translation; 

        // Check if the merge range is already used 
        const textRangeKey = `${startRow}:${startCol}:${endRow}:${endCol}`; 
        const translationRangeKey = `${startRow}:${startCol}:${endRow}:${endCol}`; 

  
        if (!textMergedRanges.has(textRangeKey)) { 
            textSheet.mergeCells(startRow, startCol, endRow, endCol); 
            textMergedRanges.add(textRangeKey); 
        } 


        if (!translationMergedRanges.has(translationRangeKey)) { 
            translationSheet.mergeCells(startRow, startCol, endRow, endCol); 
            translationMergedRanges.add(translationRangeKey); 
        } 
    }); 
  
    // Add borders to all cells 
    const addBorders = (worksheet) => { 
        worksheet.eachRow((row) => { 
            row.eachCell((cell) => { 
                cell.border = { 
                    top: { style: 'thin', color: { argb: 'FF0000' } }, // Red border 
                    bottom: { style: 'thin', color: { argb: 'FF0000' } }, 
                    left: { style: 'thin', color: { argb: 'FF0000' } }, 
                    right: { style: 'thin', color: { argb: 'FF0000' } } 
                }; 
            }); 
        }); 
    }; 

  

    addBorders(textSheet); 
    addBorders(translationSheet); 

  
    // Save the workbook to a buffer 
    const buffer = await workbook.xlsx.writeBuffer();
    return buffer; //workbook.xlsx.writeBuffer(); 

} 

 
