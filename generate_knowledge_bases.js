import fs from 'fs';

/**
 * Gera uma linha para a base de dados resumida.
 * Formato: # [ID] - [Título] - [Link]
 * @param {Object} record - O objeto do imóvel.
 * @returns {string} A linha formatada para a base resumida.
 */
function generateSummaryLine(record) {
  const id = record.listingID || 'ID_N/A';
  const title = record.title || 'Imóvel sem título';
  // Remove os caracteres '<' e '>' do link
  const link = (record.detailViewUrl || '').replace(/[<>]/g, '');

  return `# ${id} - ${title} - ${link}`;
}

/**
 * Gera uma linha para a base de dados completa.
 * Formato: # [ID] = [Título] - [Preço] - [Endereço] - [[Características]] - [Link]
 * @param {Object} record - O objeto do imóvel.
 * @returns {string} A linha formatada para a base completa.
 */
function generateCompleteLine(record) {
  const id = record.listingID || 'ID_N/A';
  const title = record.title || 'Imóvel sem título';
  const price = record.listPrice?.value || 'Sob consulta';
  const link = (record.detailViewUrl || '').replace(/[<>]/g, '');

  // 1. Consolida o endereço em uma única string, ignorando partes nulas
  const addressParts = [
    record.neighborhood,
    record.address,
    record.streetNumber,
    record.complement,
    record.postalCode
  ].filter(part => part); // Filtra valores nulos ou vazios
  const fullAddress = addressParts.join(', ');

  // 2. Consolida todas as características em uma única string separada por ';'
  const featuresParts = [];
  if (record.constructedArea?.value) featuresParts.push(`${record.constructedArea.value} m²`);
  if (record.bedrooms) featuresParts.push(`${record.bedrooms} quartos`);
  if (record.suites) featuresParts.push(`${record.suites} suítes`);
  if (record.bathrooms) featuresParts.push(`${record.bathrooms} banheiros`);
  if (record.garage?.value) featuresParts.push(`${record.garage.value} vagas`);
  if (record.features && record.features.length > 0) {
    featuresParts.push(...record.features);
  }
  const allFeaturesString = `[${featuresParts.join('; ')}]`;

  // 3. Monta a linha final com os separadores exatos que você definiu
  return `# ${id} = ${title} - ${price} - ${fullAddress} - ${allFeaturesString} - ${link}`;
}

/**
 * Função principal para ler os dados e gerar as bases de conhecimento.
 */
function main() {
  const categories = [
    { file: "apartamentos.json", category: "Apartamentos" },
    { file: "casas.json", category: "Casas" },
    { file: "sobrados.json", category: "Sobrados" },
    { file: "geminados.json", category: "Geminados" },
    { file: "outros.json", category: "Outros Tipos de Imóveis" }
  ];

  let summaryBaseContent = '';
  let completeBaseContent = '';

  console.log("Iniciando a geração das bases de conhecimento...");

  for (const { file } of categories) {
    if (!fs.existsSync(file)) {
      console.warn(`Aviso: Arquivo "${file}" não encontrado. Pulando.`);
      continue;
    }

    try {
      const rawData = fs.readFileSync(file, "utf8");
      const records = JSON.parse(rawData);

      if (records.length > 0) {
        console.log(`Processando ${records.length} imóveis de "${file}"...`);
        for (const record of records) {
          summaryBaseContent += generateSummaryLine(record) + '\n';
          completeBaseContent += generateCompleteLine(record) + '\n';
        }
      }
    } catch (error) {
      console.error(`Erro ao processar o arquivo ${file}:`, error);
    }
  }

  // Salva os dois arquivos .md, removendo a última quebra de linha
  fs.writeFileSync('base_resumida.md', summaryBaseContent.trim());
  fs.writeFileSync('base_completa.md', completeBaseContent.trim());

  console.log("\nBases de conhecimento geradas com sucesso!");
  console.log("✅ Arquivo 'base_resumida.md' criado.");
  console.log("✅ Arquivo 'base_completa.md' criado.");
}

main();