// src/utils/configLoader.js
import jsYaml from 'js-yaml';

export async function loadConfig() {
  try {
    const response = await fetch('/config/config.yaml', {cache: 'no-cache'});
    const yamlText = await response.text();
    const config = jsYaml.load(yamlText);
    return config;
  } catch (error) {
    console.error('Failed to load config:', error);
    return null;
  }
}