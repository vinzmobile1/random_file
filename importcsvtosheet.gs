function importCsvData() {
  const sheetId = "1dpjPAeA6I85e2PkJ_3TuMBhVCviSThPaw6oXg2IeSMw"; 
  let ss;
  
  try {
    ss = SpreadsheetApp.openById(sheetId);
  } catch (e) {
    Logger.log("Gagal membuka Google Sheet: " + e.message);
    return;
  }
  
  const tempSheet = ss.getSheetByName("Upload_Temp"); 
  const targetSheet = ss.getSheetByName("DB WH");     
  const folderId = "19bxpSQKALty8gRrddd5Hut9hZSChEPxi"; 
  
  if (!tempSheet || !targetSheet) {
    Logger.log("Sheet 'Upload_Temp' atau 'DB WH' tidak ditemukan.");
    return;
  }
  
  const lastRow = tempSheet.getLastRow();
  if (lastRow < 2) {
    Logger.log("Tidak ada data untuk diproses di Upload_Temp.");
    return;
  }
  
  // Ambil ID Transaksi dari sheet Upload_Temp (Kolom A / Kolom ke-1)
  const uploadId = String(tempSheet.getRange(lastRow, 1).getValue()).trim();
  
  const statusCell = tempSheet.getRange(lastRow, 3);
  const fileRelativePath = tempSheet.getRange(lastRow, 2).getValue(); 
  if (!fileRelativePath) {
    statusCell.setValue("Failed: Path file di kolom B kosong");
    return;
  }
  
  const fileName = fileRelativePath.split('/').pop(); 
  
  // Ambil semua ID yang sudah ada di sheet "DB WH" (Kolom A)
  const existingIds = new Set();
  const targetLastRow = targetSheet.getLastRow();
  if (targetLastRow >= 2) {
    const existingData = targetSheet.getRange(2, 1, targetLastRow - 1, 1).getValues();
    existingData.forEach(row => {
      if (row[0] !== "") {
        existingIds.add(String(row[0]).trim());
      }
    });
  }
  
  let folder;
  try {
    folder = DriveApp.getFolderById(folderId);
  } catch (e) {
    statusCell.setValue("Failed: Folder Drive tidak dapat diakses");
    return;
  }
  
  const files = folder.getFilesByName(fileName);
  if (!files.hasNext()) {
    statusCell.setValue("Failed: File CSV tidak ditemukan di Drive");
    return;
  }
  
  const csvFile = files.next();
  
  try {
    const blob = csvFile.getBlob();
    const csvString = blob.getDataAsString("UTF-8");
    
    // Deteksi otomatis pembatas (Koma atau Titik Koma)
    const firstLine = csvString.split('\n')[0];
    const commaCount = (firstLine.match(/,/g) || []).length;
    const semicolonCount = (firstLine.match(/;/g) || []).length;
    const delimiter = commaCount >= semicolonCount ? ',' : ';';
    
    const csvData = Utilities.parseCsv(csvString, delimiter);
    
    if (csvData.length < 2) {
      statusCell.setValue("Failed: File CSV kosong atau tidak memiliki data");
      return;
    }
    
    const sourceHeaders = csvData[0].map(h => h.trim());
    
    // Menambahkan kolom kustom "Upload ID" di bagian akhir targetHeaders
    const targetHeaders = ["No Online Order", "Customer", "Recipient", "Recipient Number", "Seller Notes", "Posting Date", "Courier Name", "Pickup Code", "Upload ID", ];
    const idHeaderIndex = targetHeaders.indexOf("No Online Order"); 
    
    // Cari indeks kolom di file CSV asli (hanya untuk 6 kolom pertama karena "Upload ID" tidak ada di file CSV)
    const headerIndices = {};
    targetHeaders.forEach(header => {
      if (header !== "Upload ID") {
        headerIndices[header] = sourceHeaders.indexOf(header);
      }
    });
    
    const rawIdIndex = headerIndices["No Online Order"];
    if (rawIdIndex === -1 || rawIdIndex === undefined) {
      statusCell.setValue("Failed: Kolom 'No Online Order' tidak ditemukan di file CSV.");
      return;
    }
    
    // Daftar Kurir yang diperbolehkan untuk diimpor
    const allowedCouriers = new Set([
      "Ambil Customer Langsung",
      "Kurir Internal",
      "Anter Aja Sameday",
      "Anteraja",
      "Anteraja Sameday",
      "Blitz-ID",
      "Gojek",
      "Gosend",
      "Gosend Instant",
      "GOSEND Instant - PICK UP",
      "GoSend Instant (Versi Lama)",
      "GoSend Instant Car - PICK UP",
      "GoSend Instant Prioritas",
      "GoSend Same Day",
      "GOSEND Sameday - PICK UP",
      "Grab",
      "Grab Instant",
      "Grab Instant - PICK UP",
      "GRAB Sameday - PICK UP",
      "GrabExpress Instant",
      "GrabExpress Instant (Versi Lama)",
      "GrabExpress Instant Prioritas",
      "GrabExpress Sameday",
      "Instant",
      "Instant Prioritas",
      "Paxel ", // Dipertahankan dari list lama Anda
      "Same Day",
      "Shipped by seller",
      "Shopee Express",
      "SPX Instant",
      "SPX Instant (Versi Lama)",
      "SPX Instant Prioritas",
      "SPX Sameday"
    ]);

    
    const rowsToAppend = [];
    let duplicateCount = 0;
    
    for (let i = 1; i < csvData.length; i++) {
      const row = csvData[i];
      if (!row || row.length === 0) continue;
      
      const currentRawId = String(row[rawIdIndex]).trim();
      if (!currentRawId) continue;
      
      // Filter Duplikat
      if (existingIds.has(currentRawId)) {
        duplicateCount++;
        continue; 
      }
      
      // Filter Berdasarkan Courier Name
      const courierIndex = headerIndices["Courier Name"];
      if (courierIndex !== -1 && courierIndex !== undefined) {
        const currentCourier = String(row[courierIndex]).trim();
        // Jika nama kurir tidak terdaftar di daftar allowedCouriers, lewati baris ini
        if (!allowedCouriers.has(currentCourier)) {
          continue;
        }
      }
      
      const newRow = [];
      targetHeaders.forEach(header => {
        // Jika kolom adalah "Upload ID", isi langsung dengan uploadId yang diambil dari Upload_Temp
        if (header === "Upload ID") {
          // Tambahkan tanda petik tunggal agar konsisten terbaca sebagai teks
          newRow.push("'" + uploadId);
          return;
        }
        
        const colIndex = headerIndices[header];
        if (colIndex !== -1 && colIndex !== undefined) {
          let val = String(row[colIndex]).trim();
          
          if (header === "No Online Order" || header === "Recipient Number") {
            if (val !== "") {
              val = val.replace(/^'/, ""); 
              val = "'" + val; 
            }
          }
          newRow.push(val);
        } else {
          newRow.push(""); 
        }
      });
      
      if (newRow.join("").trim() === "") {
        continue;
      }
      
      rowsToAppend.push(newRow);
      existingIds.add(currentRawId); 
    }
    
    // Masukkan data ke sheet "DB WH"
    if (rowsToAppend.length > 0) {
      const targetRange = targetSheet.getRange(targetSheet.getLastRow() + 1, 1, rowsToAppend.length, targetHeaders.length);
      targetRange.setValues(rowsToAppend);
      statusCell.setValue("Success: " + rowsToAppend.length + " data baru diimpor");
    } else {
      statusCell.setValue("Success: Tidak ada data baru (Semua duplikat)");
    }
    
  } catch (error) {
    statusCell.setValue("Failed: " + error.message);
  }
}
