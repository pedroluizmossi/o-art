import json
import os
import re

from comfy.comfy_core import execute_workflow # Precisaremos de uma função nova ou adaptada no comfy_core
from core.logging_core import setup_logger
from fastapi import HTTPException
from typing import Dict, Any, List, Optional

logger = setup_logger(__name__)

WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), '..', 'comfy', 'workflows')

def replace_placeholders(obj, params):
    """Função recursiva para substituir placeholders em qualquer estrutura."""
    if isinstance(obj, dict):
        return {k: replace_placeholders(v, params) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_placeholders(item, params) for item in obj]
    elif isinstance(obj, str):
        # Substitui todos placeholders do tipo {{nome}} (apenas onde for string inteira)
        match = re.fullmatch(r"\{\{(\w+)\}\}", obj)
        if match:
            key = match.group(1)
            return params.get(key, obj)
        else:
            # Substitui dentro da string, se houver algo do tipo 'prefix_{{user_id}}'
            def replacer(m):
                return str(params.get(m.group(1), m.group(0)))
            return re.sub(r"\{\{(\w+)\}\}", replacer, obj)
    else:
        return obj

def load_and_populate_workflow(workflow_name: str, params: Dict[str, Any]) -> (Dict[str, Any], str):
    """Carrega o workflow, substitui placeholders por valores reais e retorna o dict pronto."""
    workflow_path = os.path.join(WORKFLOW_DIR, workflow_name)
    if not os.path.exists(workflow_path):
        logger.error(f"Arquivo de workflow não encontrado: {workflow_path}")
        raise FileNotFoundError(f"Workflow '{workflow_name}' não encontrado.")

    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow_template = json.load(f)  # Já vira dict

    # Substitui todos os placeholders de forma segura e recursiva
    populated_workflow_dict = replace_placeholders(workflow_template, params)

    # Buscar nó de saída
    output_node_id = None
    for node_id, node_data in populated_workflow_dict.items():
        if "_meta" in node_data and "title" in node_data["_meta"]:
            if "{{output_node_id}}" in node_data["_meta"]["title"]:
                output_node_id = node_id
                break

    if not output_node_id:
        logger.warning(f"Nenhum nó de saída marcado como '{{output_node_id}}' encontrado em '{workflow_name}'.")

    return populated_workflow_dict, output_node_id



async def handle_generate_image(user_id: str, job_id: str, workflow_name: str, params: Dict[str, Any]) -> Optional[Dict[str, List[bytes]]]:
    """
    Carrega, popula e executa um workflow ComfyUI especificado.
    Retorna um dicionário mapeando node_id para lista de bytes da imagem, ou None.
    """
    logger.info(f"Iniciando geração para user {user_id}, job {job_id}, workflow {workflow_name}")
    logger.debug(f"Parâmetros recebidos: {params}")

    try:
        populated_workflow, output_node_id = load_and_populate_workflow(workflow_name, params)
        if not populated_workflow:
            raise HTTPException(status_code=400, detail="Falha ao carregar ou popular o workflow.")

        all_outputs = await execute_workflow(user_id, job_id, populated_workflow) # Passa o job_id tbm!

        if not all_outputs:
            logger.warning(f"Workflow {workflow_name} executado mas não retornou saídas.")
            return None

        if output_node_id and output_node_id in all_outputs:
            logger.info(f"Imagens geradas com sucesso pelo nó {output_node_id} para job {job_id}.")
            return {output_node_id: all_outputs[output_node_id]}
        elif all_outputs:
             logger.warning(f"Nó de saída '{output_node_id}' não encontrado nos resultados ou não definido. Retornando todas as saídas de imagem.")
             image_outputs = {k: v for k, v in all_outputs.items() if isinstance(v, list) and v and isinstance(v[0], bytes)}
             return image_outputs
        else:
            logger.error(f"Nenhuma saída de imagem encontrada para job {job_id} com workflow {workflow_name}.")
            return None


    except FileNotFoundError as e:
         logger.error(f"Erro de arquivo no handler: {e}")
         raise
    except (ValueError, KeyError, json.JSONDecodeError) as e:
         logger.error(f"Erro de dados/parâmetro no handler: {e}")
         raise HTTPException(status_code=400, detail=f"Erro nos parâmetros ou formato do workflow: {e}")
    except Exception as e:
         logger.exception(f"Erro inesperado no handle_generate_image para job {job_id}: {e}")
         raise HTTPException(status_code=500, detail="Erro interno ao processar a geração da imagem.")