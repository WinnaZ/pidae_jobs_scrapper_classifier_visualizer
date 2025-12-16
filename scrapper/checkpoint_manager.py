#!/usr/bin/env python3
"""
Checkpoint Manager for Web Scrapers
Handles saving and loading checkpoint data for resuming interrupted scraping sessions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class CheckpointManager:
    def __init__(self, scraper_name: str, checkpoint_dir: str = "checkpoints"):
        self.scraper_name = scraper_name
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_file = os.path.join(checkpoint_dir, f"{scraper_name}_checkpoint.json")
        
        # Ensure checkpoint directory exists
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(self, data: Dict[str, Any]) -> None:
        """Save checkpoint data to file"""
        checkpoint = {
            "scraper_name": self.scraper_name,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)
            print(f"💾 Checkpoint guardado: {self.checkpoint_file}")
        except Exception as e:
            print(f"❌ Error guardando checkpoint: {e}")
    
    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load checkpoint data from file"""
        if not os.path.exists(self.checkpoint_file):
            print(f"ℹ️ No se encontró checkpoint previo para {self.scraper_name}")
            return None
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            
            print(f"📂 Checkpoint encontrado de {checkpoint.get('timestamp', 'fecha desconocida')}")
            return checkpoint.get('data', {})
        except Exception as e:
            print(f"❌ Error cargando checkpoint: {e}")
            return None
    
    def clear_checkpoint(self) -> None:
        """Remove checkpoint file after successful completion"""
        if os.path.exists(self.checkpoint_file):
            try:
                os.remove(self.checkpoint_file)
                print(f"🗑️  Checkpoint eliminado: {self.checkpoint_file}")
            except Exception as e:
                print(f"❌ Error eliminando checkpoint: {e}")
    
    def has_checkpoint(self) -> bool:
        """Check if a checkpoint file exists"""
        return os.path.exists(self.checkpoint_file)


class WorkanaCheckpoint:
    """Specific checkpoint manager for Workana scraper"""
    
    @staticmethod
    def create_checkpoint_data(current_category_index: int, current_page: int, 
                             categories_completed: List[str], total_jobs_scraped: int) -> Dict[str, Any]:
        """Create checkpoint data structure for Workana"""
        return {
            "current_category_index": current_category_index,
            "current_page": current_page,
            "categories_completed": categories_completed,
            "total_jobs_scraped": total_jobs_scraped,
            "resume_mode": True
        }


class ZonaJobsCheckpoint:
    """Specific checkpoint manager for ZonaJobs scraper"""
    
    @staticmethod
    def create_checkpoint_data(current_area_index: int, current_page: int,
                             areas_completed: List[str], total_jobs_scraped: int) -> Dict[str, Any]:
        """Create checkpoint data structure for ZonaJobs"""
        return {
            "current_area_index": current_area_index,
            "current_page": current_page,
            "areas_completed": areas_completed,
            "total_jobs_scraped": total_jobs_scraped,
            "resume_mode": True
        }


class ComputrabajoCheckpoint:
    """Specific checkpoint manager for Computrabajo scraper"""
    
    @staticmethod
    def create_checkpoint_data(current_area_index: int, current_page: int,
                             areas_completed: List[str], total_jobs_scraped: int) -> Dict[str, Any]:
        """Create checkpoint data structure for Computrabajo"""
        return {
            "current_area_index": current_area_index,
            "current_page": current_page,
            "areas_completed": areas_completed,
            "total_jobs_scraped": total_jobs_scraped,
            "resume_mode": True
        }


class LinkedInCheckpoint:
    """Specific checkpoint manager for LinkedIn scraper"""
    
    @staticmethod
    def create_checkpoint_data(current_area_index: int, current_page: int,
                             areas_completed: List[str], total_jobs_scraped: int) -> Dict[str, Any]:
        """Create checkpoint data structure for LinkedIn"""
        return {
            "current_area_index": current_area_index,
            "current_page": current_page,
            "areas_completed": areas_completed,
            "total_jobs_scraped": total_jobs_scraped,
            "resume_mode": True
        }


def ask_user_resume_choice(checkpoint_data: Dict[str, Any], scraper_name: str) -> bool:
    """Ask user if they want to resume from checkpoint"""
    print(f"\n🔄 CHECKPOINT ENCONTRADO para {scraper_name}")
    print("="*60)
    
    if scraper_name.lower() == "workana":
        print(f" Progreso anterior:")
        print(f"   - Categorías completadas: {len(checkpoint_data.get('categories_completed', []))}")
        print(f"   - Categoría actual: #{checkpoint_data.get('current_category_index', 0) + 1}")
        print(f"   - Página actual: {checkpoint_data.get('current_page', 1)}")
        print(f"   - Jobs recolectados: {checkpoint_data.get('total_jobs_scraped', 0)}")
    else:
        print(f" Progreso anterior:")
        print(f"   - Áreas completadas: {len(checkpoint_data.get('areas_completed', []))}")
        print(f"   - Área actual: #{checkpoint_data.get('current_area_index', 0) + 1}")
        print(f"   - Página actual: {checkpoint_data.get('current_page', 1)}")
        print(f"   - Jobs recolectados: {checkpoint_data.get('total_jobs_scraped', 0)}")
    
    print("="*60)
    
    while True:
        choice = input("\n¿Deseas continuar desde donde se quedó? (s/n): ").lower().strip()
        if choice in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print("Por favor responde 's' para sí o 'n' para no")


def get_resume_info(scraper_name: str) -> tuple:
    """
    Get resume information for any scraper
    Returns: (should_resume, checkpoint_data, checkpoint_manager)
    """
    checkpoint_manager = CheckpointManager(scraper_name)
    
    if not checkpoint_manager.has_checkpoint():
        return False, None, checkpoint_manager
    
    checkpoint_data = checkpoint_manager.load_checkpoint()
    if not checkpoint_data:
        return False, None, checkpoint_manager
    
    should_resume = ask_user_resume_choice(checkpoint_data, scraper_name)
    
    if not should_resume:
        checkpoint_manager.clear_checkpoint()
        return False, None, checkpoint_manager
    
    return True, checkpoint_data, checkpoint_manager