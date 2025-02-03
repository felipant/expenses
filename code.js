function doPost(e) {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("dados");
    var data = JSON.parse(e.postData.contents);
    var parcelas = parseFloat(data.parcelas);
    var valor = parseFloat(data.valor);
    var valor_parcela = valor/parcelas;
    var data_da_compra_str = data.data_compra;
    var data_da_compra = new Date(data_da_compra_str);
    if (parcelas == 1) {
      sheet.appendRow([new Date(), data.data_compra, data.valor, data.parcelas, data.categoria, data.subcategoria, data.tipo, data.comentario]); // Modify for more fields
    } else {
      var arrayParcelas = parcelamento(data_da_compra,parcelas);
      for (var i = 1; i <= parcelas; i++) {
        sheet.appendRow([new Date(), arrayParcelas[i-1], valor_parcela, i, data.categoria, data.subcategoria, data.tipo, data.comentario]);
      };
    }
    return ContentService.createTextOutput("Success").setMimeType(ContentService.MimeType.TEXT);
}