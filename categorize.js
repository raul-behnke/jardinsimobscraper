import fs from 'fs';

// Função que categoriza os registros com base no campo tipologia
function categorizeListings(listings) {
  const categories = {};

  listings.forEach(item => {
    // Pega o valor da tipologia e normaliza para minúsculas
    const tipologia = item.tipologia ? item.tipologia.toLowerCase() : "outros";
    let category = "outros";

    if (tipologia.includes("apartamento")) {
      category = "apartamentos";
    } else if (tipologia.includes("casa")) {
      category = "casas";
    } else if (tipologia.includes("geminado")) {
      category = "geminados";
    } else if (tipologia.includes("sobrado")) {
      category = "sobrados";
    }

    // Se a categoria ainda não existir, cria um array para ela
    if (!categories[category]) {
      categories[category] = [];
    }
    categories[category].push(item);
  });

  return categories;
}

function main() {
  try {
    // Lê o arquivo JSON com os dados dos empreendimentos
    const listings = JSON.parse(fs.readFileSync("output.json", "utf8"));
    
    // Categoriza os registros
    const categories = categorizeListings(listings);

    // Para cada categoria, gera um arquivo JSON com os registros correspondentes
    Object.keys(categories).forEach(category => {
      const fileName = `${category}.json`;
      fs.writeFileSync(fileName, JSON.stringify(categories[category], null, 2));
      console.log(`Arquivo "${fileName}" gerado com ${categories[category].length} registros.`);
    });
  } catch (error) {
    console.error("Erro ao processar os dados:", error);
  }
}

main();
