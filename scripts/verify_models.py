#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_model(model_path, test_input, model_type="qwen"):
    """Verify model can load and generate text"""
    try:
        logger.info(f"Loading model from {model_path}")
        
        # Check if model path exists
        if not os.path.exists(model_path):
            logger.error(f"Model path does not exist: {model_path}")
            return False
            
        # Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # Load model in CPU mode with FP16
        logger.info("Loading model in CPU mode...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="cpu"
        )
        
        # Test generation
        logger.info("Generating test output...")
        inputs = tokenizer(test_input, return_tensors="pt")
        outputs = model.generate(
            inputs["input_ids"],
            max_length=100,
            num_return_sequences=1,
            temperature=0.7
        )
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        logger.info(f"Generated text: {generated_text}")
        return True
        
    except Exception as e:
        logger.error(f"Model verification failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Verify all models"""
    models_to_verify = {
        "models/qwen/base/qwen/Qwen-7B-Chat": "写一个简短的故事关于一只小猫"
    }
    
    success = True
    for model_path, test_input in models_to_verify.items():
        logger.info(f"Verifying model in {model_path}")
        if not verify_model(model_path, test_input):
            success = False
            
    if success:
        logger.info("All models verified successfully!")
    else:
        logger.error("Some models failed verification. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main() 