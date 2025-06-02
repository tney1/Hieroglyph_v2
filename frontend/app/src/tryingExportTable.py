"""

function exportToExcel(data) { 

    // Determine the maximum x and y values to scale the grid 
    let maxX = 0; 
    let maxY = 0; 
    data.boxes.forEach(box => { 
        maxX = Math.max(maxX, box.x + box.w); 
        maxY = Math.max(maxY, box.y + box.h); 
    }); 

    // Introduce a scaling factor for width 
    const widthScalingFactor = 0.2; // Adjust this value as needed (e.g., 0.5 means half the scaling) 

    // Create a new workbook 
    const workbook = XLSX.utils.book_new(); 

  

    // Create two sheets: one for text and one for translation 
    const textSheetData = []; 
    const translationSheetData = []; 

    // Store merges for each sheet 
    const textMerges = []; 
    const translationMerges = []; 


    data.boxes.forEach(box => { 
        // Calculate the starting position of the box in the sheet 
        const startRow = Math.floor((box.y / maxY) * 100); 
        const startCol = Math.floor((box.x / maxX) * 100 * widthScalingFactor); 

        // Calculate the ending position of the box in the sheet 
        const endRow = Math.floor(((box.y + box.h) / maxY) * 100) - 1; 
        const endCol = Math.floor(((box.x + box.w) / maxX) * 100 * widthScalingFactor) - 1; 

        // Ensure the sheet data arrays are large enough to accommodate the cell positions 
        while (textSheetData.length <= endRow) textSheetData.push([]); 
        while (translationSheetData.length <= endRow) translationSheetData.push([]); 

        for (let r = startRow; r <= endRow; r++) { 
            if (!textSheetData[r]) textSheetData[r] = []; 
            if (!translationSheetData[r]) translationSheetData[r] = []; 
            while (textSheetData[r].length <= endCol) textSheetData[r].push(null); 
            while (translationSheetData[r].length <= endCol) translationSheetData[r].push(null); 
        } 

        // Place the text and translation in the correct starting cell 
        textSheetData[startRow][startCol] = box.text; 
        translationSheetData[startRow][startCol] = box.translation; 

        // Add merges for the text sheet 
        textMerges.push({ s: { r: startRow, c: startCol }, e: { r: endRow, c: endCol } }); 

        // Add merges for the translation sheet 
        translationMerges.push({ s: { r: startRow, c: startCol }, e: { r: endRow, c: endCol } }); 
    }); 
  

    // Remove empty rows 
    const trimEmptyRows = (sheetData) => { 
        while (sheetData.length > 0 && sheetData[0].every(cell => cell === null)) { 
            sheetData.shift(); // Remove the first row 
        } 
    }; 

  

    trimEmptyRows(textSheetData); 

    trimEmptyRows(translationSheetData); 

    // Remove empty columns 
    const trimEmptyColumns = (sheetData) => { 
        const columnCount = sheetData[0]?.length || 0; 
        let firstNonEmptyColumn = columnCount; 
        sheetData.forEach(row => { 
            row.forEach((cell, colIndex) => { 
                if (cell !== null && colIndex < firstNonEmptyColumn) { 
                    firstNonEmptyColumn = colIndex; 
                } 
            }); 
        }); 
        sheetData.forEach(row => { 
            row.splice(0, firstNonEmptyColumn); // Remove empty columns from the start 
        }); 
    }; 
    trimEmptyColumns(textSheetData); 
    trimEmptyColumns(translationSheetData); 

    // Convert the sheet objects to worksheets 
    const textWorksheet = XLSX.utils.aoa_to_sheet(textSheetData); 
    const translationWorksheet = XLSX.utils.aoa_to_sheet(translationSheetData); 
    // Add borders to all cells 
    const addBorders = (worksheet) => { 
        const range = XLSX.utils.decode_range(worksheet['!ref']); 
        for (let row = range.s.r; row <= range.e.r; row++) { 
            for (let col = range.s.c; col <= range.e.c; col++) { 
                const cellAddress = XLSX.utils.encode_cell({ r: row, c: col }); 
                if (!worksheet[cellAddress]) continue; // Skip empty cells 
                worksheet[cellAddress].s = { 
                    border: { 
                        top: { style: "thick", color: { rgb: "FF0000" } }, 
                        bottom: { style: "thick", color: { rgb: "FF0000" } }, 
                        left: { style: "thick", color: { rgb: "FF0000" } }, 
                        right: { style: "thick", color: { rgb: "FF0000" } } 
                    } 
                }; 
            } 
        } 
    }; 

  

    addBorders(textWorksheet); 

    addBorders(translationWorksheet); 

  

    // Assign the data and merges to the worksheets 

    textWorksheet['!merges'] = textMerges; 

    translationWorksheet['!merges'] = translationMerges; 

  

    // Append sheets to the workbook 

    XLSX.utils.book_append_sheet(workbook, textWorksheet, 'Text'); 

    XLSX.utils.book_append_sheet(workbook, translationWorksheet, 'Translation'); 

  

    // Generate Excel file as a binary string 

    const wbout = XLSX.write(workbook, { bookType: 'xlsx', type: 'binary' }); 

  

    // Convert binary string to array buffer 

    function s2ab(s) { 

        const buf = new ArrayBuffer(s.length); 

        const view = new Uint8Array(buf); 

        for (let i = 0; i < s.length; i++) { 

            view[i] = s.charCodeAt(i) & 0xFF; 

        } 

        return buf; 

    } 

  

    data = s2ab(wbout); 

    return data; 

} 





























/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // Function to cluster boxes into tables using hierarchical clustering
    function clusterBoxes(boxes, numberOfClusters) {
        const points = boxes.map(box => [box.x, box.y]);

        const { agnes } = require('ml-hclust');
        // Perform hierarchical clustering using agnes
        const tree = agnes(points, {
            method: 'ward', // You can choose other methods like 'single', 'complete', 'average', etc.
        });

        // Function to cut the dendrogram to form clusters
        function cutDendrogram(node, clusters, currentCluster) {
            if (node.isLeaf) {
                clusters[node.index] = currentCluster;
            } else {
                if (currentCluster < numberOfClusters - 1) {
                    cutDendrogram(node.children[0], clusters, currentCluster);
                    currentCluster++;
                    cutDendrogram(node.children[1], clusters, currentCluster);
                } else {
                    // Assign all remaining nodes to the current cluster
                    assignCluster(node, clusters, currentCluster);
                }
            }
        }

        function assignCluster(node, clusters, clusterId) {
            if (node.isLeaf) {
                clusters[node.index] = clusterId;
            } else {
                assignCluster(node.children[0], clusters, clusterId);
                assignCluster(node.children[1], clusters, clusterId);
            }
        }

        const clusterIndices = new Array(points.length).fill(-1);
        cutDendrogram(tree, clusterIndices, 0);

        // Group boxes by cluster
        const clusteredBoxes = Array.from({ length: numberOfClusters }, () => []);
        clusterIndices.forEach((clusterId, index) => {
            clusteredBoxes[clusterId].push(boxes[index]);
        });

        return clusteredBoxes;
    }

    // Cluster the boxes
    const numberOfClusters = 2; // Define how many clusters you want
    const clusters = clusterBoxes(data.boxes, numberOfClusters);

    // Create a new workbook
    const wb = XLSX.utils.book_new();

    // Process each cluster as a separate table
    clusters.forEach((cluster, index) => {
        // Determine the maximum number of rows and columns needed
        let maxRow = 0;
        let maxCol = 0;

        cluster.forEach(box => {
            const endRow = Math.floor((box.y + box.h) * 100); // Scale to a larger grid
            const endCol = Math.floor((box.x + box.w) * 100); // Scale to a larger grid
            if (endRow > maxRow) maxRow = endRow;
            if (endCol > maxCol) maxCol = endCol;
        });

        // Initialize worksheets as arrays of arrays
        const textData = Array.from({ length: maxRow + 1 }, () => Array(maxCol + 1).fill(null));
        const translationData = Array.from({ length: maxRow + 1 }, () => Array(maxCol + 1).fill(null));

        // Populate worksheets using scaled x and y coordinates
        cluster.forEach(box => {
            const startCol = Math.floor(box.x * 100);
            const startRow = Math.floor(box.y * 100);
            const endCol = Math.floor((box.x + box.w) * 100) - 1;
            const endRow = Math.floor((box.y + box.h) * 100) - 1;

            // Place text data
            textData[startRow][startCol] = box.text;

            // Place translation data
            translationData[startRow][startCol] = box.translation;

            // Add merge information
            function addMerge(ws, startRow, startCol, endRow, endCol) {
                ws['!merges'] = ws['!merges'] || [];
                ws['!merges'].push({
                    s: { r: startRow, c: startCol },
                    e: { r: endRow, c: endCol }
                });
            }

            addMerge(textData, startRow, startCol, endRow, endCol);
            addMerge(translationData, startRow, startCol, endRow, endCol);
        });

        """