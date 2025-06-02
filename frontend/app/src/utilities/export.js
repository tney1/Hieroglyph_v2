// import * as XLSX from 'xlsx';


const header = "name,page,box,text,translation\n"
export function downloadDataFile(data, filename) {
    const url = window.URL.createObjectURL(new Blob([data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
}
export function downloadPicture(pictureURL, filename) {
    const link = document.createElement('a');
    link.href = pictureURL;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
}


async function exportToExcel(data, pageNumber, exportAllPages) { 

    const ExcelJS = require('exceljs'); 
    const workbook = new ExcelJS.Workbook();

        const processPage = (pageData, pageNumber) => {

        if (pageData.boxes.length < 1){
            return;
        }
        let maxX = 0; 
        let maxY = 0; 
        let minX = Infinity;
        let minY = Infinity;

        pageData.boxes.forEach(box => { 
            maxX = Math.max(maxX, box.x + box.w); 
            maxY = Math.max(maxY, box.y + box.h); 

            minX = Math.min(minX, box.x);   
            minY = Math.min(minY, box.y);
        }); 

        pageData.boxes.forEach(box => {
            box.x -= minX;
            box.y -=minY;
        })
        
        const widthScalingFactor = 0.2; // Adjust this value as needed 
        const heightScalingFactor = 0.5; // could add these under "Advanced Options"
        // // Create a new workbook 
        // const workbook = new ExcelJS.Workbook(); 
        let textSheet = workbook.addWorksheet('Page '+ pageNumber.toString() +' Text'); 
        let translationSheet = workbook.addWorksheet('Page '+ pageNumber.toString() +' Translation'); 

        const textMergedRanges = new Set(); 
        const translationMergedRanges = new Set(); 

        pageData.boxes.forEach(box => { 

            console.log("TextText: ", box.text, "Translation: ", box.translation);

            // Calculate the starting position of the box in the sheet 
            const startRow = Math.floor((box.y / maxY) * 100 * heightScalingFactor) + 1; // ExcelJS rows are 1-based 
            const startCol = Math.floor((box.x / maxX) * 100 * widthScalingFactor) + 1; // ExcelJS columns are 1-based 
            // Calculate the ending position of the box in the sheet 
            const endRow = Math.floor(((box.y + box.h) / maxY) * 100 * heightScalingFactor); 
            const endCol = Math.floor(((box.x + box.w) / maxX) * 100 * widthScalingFactor); 
    
            // Check if the merge range is already used 
            const textRangeKey = `${startRow}:${startCol}:${endRow}:${endCol}`; 
            const translationRangeKey = `${startRow}:${startCol}:${endRow}:${endCol}`; 

            if (textMergedRanges.has(textRangeKey)) { 
                console.warn('Duplicate or overlapping boxes detected');
                return;
            }
            if (translationMergedRanges.has(translationRangeKey)) { 
                console.warn('Duplicate or overlapping boxes detected');
                return;
            }

            // Place the text and translation in the correct starting cell 
            textSheet.getCell(startRow, startCol).value = box.text; 
            if (box.translation !== ""){
                translationSheet.getCell(startRow, startCol).value = box.translation; 
            }
            else {
                translationSheet.getCell(startRow, startCol).value = "Don't forget to Translate!"; 
            }
            try {
                textSheet.mergeCells(startRow, startCol, endRow, endCol); 
                textMergedRanges.add(textRangeKey); 
                translationSheet.mergeCells(startRow, startCol, endRow, endCol); 
                translationMergedRanges.add(translationRangeKey); 
            } catch (error){
                console.error('Error merging cells');
                console.error(error.message);
                // window.alert('Duplicate or overlapping bounding boxes were detected in page ${pageNumber}: ${error.message}. Please verify the exported data is correct');
                // throw new Error('Duplicate or overlapping cells in page ${pageNumber}. Please check the data');
            }

        }); 
    
        // Add borders to each cell
        const addBorders = (worksheet) => { 
            worksheet.eachRow((row) => { 
                row.eachCell((cell) => { 
                    cell.border = { 
                        top: { style: 'thin', color: { argb: 'FF000000' } },
                        bottom: { style: 'thin', color: { argb: 'FF000000' } }, 
                        left: { style: 'thin', color: { argb: 'FF000000' } }, 
                        right: { style: 'thin', color: { argb: 'FF000000' } } 
                    }; 
                }); 
            }); 
        }; 

        addBorders(textSheet); 
        addBorders(translationSheet); 
    };

    try {
        if(exportAllPages){
            Object.keys(data).forEach((pageKey) => {
                const pageData = data[pageKey];
                processPage(pageData, pageKey);
            });
        }
        else {
            processPage(data, pageNumber);
        } 
            // Save the workbook to a buffer 
        const buffer = await workbook.xlsx.writeBuffer();
        return buffer; //workbook.xlsx.writeBuffer();    
    } catch (error) {
        console.error(error.message);
        alert('Export Failed'); //: ${error.message}
        throw error;
    }
} 
      

function quoteCSV(str) {
    if (str) {
        let newStr = str.replace(/(\r\n|\n|\r|\s+|\t|&nbsp)/gm, ' ');
        newStr = newStr.replace(/,/g, '\\,');
        newStr = newStr.replace(/"/g, '""');
        newStr = newStr.replace(/'/g, "\\'");
        newStr = newStr.replace(/ +(?= )/g, '');
        return `"${newStr}"`;
    } else {
        return str
    }
}

function convertAllPagesToCSV(data, selectedFile) {
    const keysRow = Object.keys(data)
    console.log("convertAllPagesToCSVData:", data);
    const allData = keysRow.map((key) => {
        return data[key].boxes.map((box, boxIndex) => {
            if(box && box.text) {
                return `${selectedFile.name},${key},${boxIndex},${quoteCSV(box.text)},${quoteCSV(box.translation)}`
            }
            else{
                return "";
            }
        }).join("\n");
    }).join("\n");
    console.log("convertAllPagesToCSV converted all data:", allData)
    return header + allData;
}
function convertCurrentPageToCSV(data, pageNumber, selectedFile) {
    console.log("convertCurrentPageToCSV Data:", data);
    const allData = data.boxes.map((box, boxIndex) => {
        if(box && box.text) { 
            return `${selectedFile.name},${pageNumber},${boxIndex},${quoteCSV(box.text)},${quoteCSV(box.translation)}`
        }
        else{
            return "";
        }
    }).join("\n");
    console.log("convertCurrentPageToCSV converted all data:", allData)
    return header + allData;
}

function convertRowToCSV(data, boxIndex, pageNumber, selectedFile) {
    console.log("convertRowToCSV Data:", data, boxIndex, pageNumber);
    const box = data.boxes.at(boxIndex)
    console.log("convertRowToCSV converted box:", box)
    return `${selectedFile.name},${pageNumber},${boxIndex},${quoteCSV(box.text)}${box.translation ? ","+quoteCSV(box.translation) : ""}\n`;
}

async function exportFunction(exportType, exportAllPages, selectedFile, pageNumber, allPages) {
    let data, filename;
    if (exportAllPages) {
        if (exportType === 'csv') {
            data = convertAllPagesToCSV(allPages, selectedFile);
            console.log("exportFunction allpages csv: ", data)
            filename = `${selectedFile.name}.csv`;
        } else if (exportType === 'json') {
            data = JSON.stringify(allPages, null, ' ');
            console.log("exportFunction allpages json: ", data)
            filename = `${selectedFile.name}.json`;
        } else if (exportType === 'excel') {
            data = await exportToExcel(allPages, pageNumber, exportAllPages);
            console.log("exportFunction page excel: ", data)
            filename = `${selectedFile.name}.xlsx`
        }
    } else {
        if (exportType === 'csv') {
            data = convertCurrentPageToCSV(allPages[pageNumber], pageNumber, selectedFile);
            console.log("exportFunction page csv: ", data)
            filename = `${selectedFile.name}.${pageNumber}.csv`
        } else if (exportType === 'json') {
            data = JSON.stringify(allPages[pageNumber], null, ' ');
            console.log("exportFunction page json: ", data)
            filename = `${selectedFile.name}.${pageNumber}.json`
        } else if (exportType === 'excel') {
            data = await exportToExcel(allPages[pageNumber], pageNumber, exportAllPages);
            console.log("exportFunction page excel: ", data)
            filename = `${selectedFile.name}.${pageNumber}.xlsx`
        }
    }
    downloadDataFile(data, filename);
}
export {exportFunction, convertCurrentPageToCSV, convertAllPagesToCSV, convertRowToCSV}