// Se estiver utilizando Node.js v18+, o fetch já está disponível.
// Para versões anteriores, descomente a linha abaixo:
// const fetch = require('node-fetch');

import { DOMParser } from 'xmldom';
import fs from 'fs';

// URL do XML remoto
const xmlUrl = 'https://restrito.casteldigital.com.br/vivareal_open/jardins.imb.br-vivareal.xml?auth=jEzonWGJdq';

// Função para buscar o XML a partir da URL
async function fetchXML(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Erro ao buscar XML: ${response.statusText}`);
  }
  return await response.text();
}

// Função auxiliar para obter o texto do primeiro elemento com a tag informada dentro do namespace
function getNodeText(node, NS, tagName) {
  return node.getElementsByTagNameNS(NS, tagName)[0]?.textContent || null;
}

// Função auxiliar para obter o valor de um atributo de um nó
function getNodeAttribute(node, attribute) {
  return node?.getAttribute(attribute) || null;
}

// Função que converte o XML para JSON com os campos desejados
function convertXMLtoJSON(xmlString) {
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(xmlString, "application/xml");

  // Namespace definido no XML
  const NS = "http://www.vivareal.com/schemas/1.0/VRSync";

  // Array que armazenará os dados resumidos
  const listingsArray = [];

  // Seleciona todos os elementos <Listing> considerando o namespace
  const listings = xmlDoc.getElementsByTagNameNS(NS, "Listing");

  for (let i = 0; i < listings.length; i++) {
    const listing = listings[i];

    // Campos do nível superior
    const listingID = getNodeText(listing, NS, "ListingID");
    const title = getNodeText(listing, NS, "Title");
    const detailViewUrl = getNodeText(listing, NS, "DetailViewUrl");

    // Nó Details (contém vários campos)
    const detailsNode = listing.getElementsByTagNameNS(NS, "Details")[0];
    const tipologia = detailsNode ? getNodeText(detailsNode, NS, "Tipologia") : null;
    const description = detailsNode ? getNodeText(detailsNode, NS, "Description") : null;

    const listPriceNode = detailsNode ? detailsNode.getElementsByTagNameNS(NS, "ListPrice")[0] : null;
    const listPrice = listPriceNode ? listPriceNode.textContent : null;
    const listPriceCurrency = listPriceNode ? getNodeAttribute(listPriceNode, "currency") : null;

    const propertyAdministrationFeeNode = detailsNode ? detailsNode.getElementsByTagNameNS(NS, "PropertyAdministrationFee")[0] : null;
    const propertyAdministrationFee = propertyAdministrationFeeNode ? propertyAdministrationFeeNode.textContent : null;
    const propertyAdministrationFeeCurrency = propertyAdministrationFeeNode ? getNodeAttribute(propertyAdministrationFeeNode, "currency") : null;

    const constructedAreaNode = detailsNode ? detailsNode.getElementsByTagNameNS(NS, "ConstructedArea")[0] : null;
    const constructedArea = constructedAreaNode ? constructedAreaNode.textContent : null;
    const constructedAreaUnit = constructedAreaNode ? getNodeAttribute(constructedAreaNode, "unit") : null;

    const livingAreaNode = detailsNode ? detailsNode.getElementsByTagNameNS(NS, "LivingArea")[0] : null;
    const livingArea = livingAreaNode ? livingAreaNode.textContent : null;
    const livingAreaUnit = livingAreaNode ? getNodeAttribute(livingAreaNode, "unit") : null;

    const lotAreaNode = detailsNode ? detailsNode.getElementsByTagNameNS(NS, "LotArea")[0] : null;
    const lotArea = lotAreaNode ? lotAreaNode.textContent : null;
    const lotAreaUnit = lotAreaNode ? getNodeAttribute(lotAreaNode, "unit") : null;

    const bedrooms = detailsNode ? getNodeText(detailsNode, NS, "Bedrooms") : null;
    const bathrooms = detailsNode ? getNodeText(detailsNode, NS, "Bathrooms") : null;
    const suites = detailsNode ? getNodeText(detailsNode, NS, "Suites") : null;

    const garageNode = detailsNode ? detailsNode.getElementsByTagNameNS(NS, "Garage")[0] : null;
    const garage = garageNode ? garageNode.textContent : null;
    const garageType = garageNode ? getNodeAttribute(garageNode, "type") : null;

    // Coleta todas as Features
    let features = [];
    const featuresNode = detailsNode ? detailsNode.getElementsByTagNameNS(NS, "Features")[0] : null;
    if (featuresNode) {
      const featureNodes = featuresNode.getElementsByTagNameNS(NS, "Feature");
      for (let j = 0; j < featureNodes.length; j++) {
        features.push(featureNodes[j].textContent);
      }
    }

    // Nó Location (contém dados de endereço)
    const locationNode = listing.getElementsByTagNameNS(NS, "Location")[0];
    const neighborhood = locationNode ? getNodeText(locationNode, NS, "Neighborhood") : null;
    const address = locationNode ? getNodeText(locationNode, NS, "Address") : null;
    const streetNumber = locationNode ? getNodeText(locationNode, NS, "StreetNumber") : null;
    const complement = locationNode ? getNodeText(locationNode, NS, "Complement") : null;
    const postalCode = locationNode ? getNodeText(locationNode, NS, "PostalCode") : null;

    // Monta o objeto com os dados desejados
    const listingData = {
      listingID,
      title,
      detailViewUrl,
      tipologia,
      description,
      listPrice: {
        value: listPrice,
        currency: listPriceCurrency
      },
      propertyAdministrationFee: propertyAdministrationFee ? {
        value: propertyAdministrationFee,
        currency: propertyAdministrationFeeCurrency
      } : null,
      constructedArea: {
        value: constructedArea,
        unit: constructedAreaUnit
      },
      livingArea: {
        value: livingArea,
        unit: livingAreaUnit
      },
      lotArea: {
        value: lotArea,
        unit: lotAreaUnit
      },
      bedrooms,
      bathrooms,
      suites,
      garage: {
        value: garage,
        type: garageType
      },
      features,
      neighborhood,
      address,
      streetNumber,
      complement,
      postalCode
    };

    listingsArray.push(listingData);
  }

  return listingsArray;
}

// Função principal para executar o fluxo
async function main() {
  try {
    console.log("Buscando XML...");
    const xmlString = await fetchXML(xmlUrl);

    console.log("Convertendo XML para JSON...");
    const jsonData = convertXMLtoJSON(xmlString);

    const jsonOutput = JSON.stringify(jsonData, null, 2);

    // Grava o JSON em um arquivo chamado output.json
    fs.writeFile('output.json', jsonOutput, (err) => {
      if (err) throw err;
      console.log('Arquivo "output.json" gerado com sucesso!');
    });
  } catch (error) {
    console.error('Erro:', error);
  }
}

main();
