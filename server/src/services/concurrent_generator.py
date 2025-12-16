"""
Module hỗ trợ sinh câu hỏi song song với threading
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass
from threading import Semaphore


@dataclass
class TaskResult:
    """Kết quả của một task"""
    success: bool
    data: Any
    error: Optional[str] = None
    task_id: str = ""


class ConcurrentGenerator:
    """Class quản lý việc sinh câu hỏi song song với threading"""
    
    def __init__(self, max_workers: int = 10, min_interval: float = 0.3):
        """
        Khởi tạo Concurrent Generator
        
        Args:
            max_workers: Số lượng threads tối đa chạy đồng thời
            min_interval: Khoảng thời gian tối thiểu giữa 2 lần bắt đầu request (giây)
        """
        self.max_workers = max_workers
        self.min_interval = min_interval
        self.semaphore = Semaphore(max_workers)
        self.start_times = []
    
    def _throttle_request(self):
        """
        Throttle request để tránh quá tải - không block hoàn toàn
        Chỉ đảm bảo khoảng cách tối thiểu giữa các lần BẮT ĐẦU request
        """
        if self.min_interval > 0 and len(self.start_times) > 0:
            elapsed = time.time() - self.start_times[-1]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        
        self.start_times.append(time.time())
        
        # Giữ lại tối đa 100 timestamps
        if len(self.start_times) > 100:
            self.start_times = self.start_times[-100:]
    
    def process_batch(self, 
                     tasks: List[Dict],
                     process_func: Callable,
                     progress_callback: Optional[Callable] = None) -> List[TaskResult]:
        """
        Xử lý một batch tasks song song
        
        Args:
            tasks: List các task dict chứa thông tin cần xử lý
            process_func: Function xử lý một task (nhận task dict, trả về kết quả)
            progress_callback: Function callback khi hoàn thành một task (nhận completed, total)
            
        Returns:
            List[TaskResult]: Danh sách kết quả
        """
        results = []
        total_tasks = len(tasks)
        completed = 0
        
        print(f"🚀 Xử lý {total_tasks} tasks song song (max {self.max_workers} workers)\n")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tất cả tasks
            future_to_task = {
                executor.submit(
                    self._process_single_task,
                    task,
                    process_func
                ): task
                for task in tasks
            }
            
            # Xử lý kết quả khi hoàn thành
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                task_id = task.get('id', 'unknown')
                num_q = task.get('num_questions', 1)
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    completed += 1
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(completed, total_tasks, result)
                    
                    # Hiển thị tiến độ gọn
                    status = "✅" if result.success else "❌"
                    
                    # Xác định số câu được sinh
                    if result.success and result.data:
                        if isinstance(result.data, list):
                            num_generated = len(result.data)
                        else:
                            num_generated = 1  # DS question (single object)
                    else:
                        num_generated = 0
                    
                    print(f"{status} [{completed}/{total_tasks}] {task_id} → {num_generated} câu")
                    
                    if not result.success and result.error:
                        print(f"   ⚠️  {result.error[:80]}")
                
                except Exception as e:
                    error_result = TaskResult(
                        success=False,
                        data=None,
                        error=str(e),
                        task_id=task_id
                    )
                    results.append(error_result)
                    completed += 1
                    
                    print(f"❌ [{completed}/{total_tasks}] {task_id} - {str(e)[:80]}")
        
        # Thống kê
        success_count = sum(1 for r in results if r.success)
        fail_count = total_tasks - success_count
        
        print(f"\n📊 Kết quả: {success_count} thành công, {fail_count} thất bại")
        
        return results
    
    def _process_single_task(self, task: Dict, process_func: Callable) -> TaskResult:
        """
        Xử lý một task đơn lẻ với throttling
        
        Args:
            task: Task dict
            process_func: Function xử lý task
            
        Returns:
            TaskResult: Kết quả
        """
        task_id = task.get('id', 'unknown')
        
        try:
            # Throttle trước khi bắt đầu request
            self._throttle_request()
            
            # Gọi function (KHÔNG lock ở đây, cho phép song song)
            result = process_func(task)
            
            return TaskResult(
                success=True,
                data=result,
                task_id=task_id
            )
        
        except Exception as e:
            return TaskResult(
                success=False,
                data=None,
                error=str(e),
                task_id=task_id
            )


def generate_tn_questions_parallel(generator, 
                                   tn_specs: List,
                                   prompt_template_path: str,
                                   max_workers: int = 5,
                                   min_interval: float = 0.2,
                                   verbose: bool = False,
                                   max_retries: int = 3,
                                   retry_delay: float = 2.0) -> List:
    """
    Sinh câu hỏi TN song song
    
    Args:
        generator: QuestionGenerator instance
        tn_specs: List QuestionSpec cho câu TN
        prompt_template_path: Đường dẫn prompt template
        max_workers: Số threads tối đa
        min_interval: Khoảng thời gian tối thiểu giữa các lần bắt đầu request (giây)
        verbose: Hiển thị logs chi tiết
        max_retries: Số lần retry tối đa khi gặp lỗi
        retry_delay: Delay giữa các lần retry (giây)
        
    Returns:
        List: Danh sách các GeneratedQuestion
    """
    # Set verbose mode
    generator.verbose = verbose
    generator.max_retries = max_retries
    generator.retry_delay = retry_delay
    
    # Chuẩn bị tasks
    tasks = [
        {
            'id': f"{spec.question_codes[0] if spec.question_codes else f'TN-{i+1}'}",
            'spec': spec,
            'template_path': prompt_template_path,
            'num_questions': spec.num_questions
        }
        for i, spec in enumerate(tn_specs)
    ]
    
    # Function xử lý một task
    def process_tn_task(task):
        return generator.generate_questions_for_spec(
            spec=task['spec'],
            prompt_template_path=task['template_path']
        )
    
    # Xử lý song song
    concurrent_gen = ConcurrentGenerator(
        max_workers=max_workers,
        min_interval=min_interval
    )
    
    results = concurrent_gen.process_batch(
        tasks=tasks,
        process_func=process_tn_task
    )
    
    # Flatten kết quả
    all_questions = []
    for result in results:
        if result.success and result.data:
            all_questions.extend(result.data)
    
    return all_questions


def generate_ds_questions_parallel(generator,
                                   ds_specs: List,
                                   prompt_template_path: str,
                                   max_workers: int = 5,
                                   min_interval: float = 0.2,
                                   verbose: bool = False,
                                   max_retries: int = 3,
                                   retry_delay: float = 2.0) -> List:
    """
    Sinh câu hỏi DS song song
    
    Args:
        generator: QuestionGenerator instance
        ds_specs: List TrueFalseQuestionSpec cho câu DS
        prompt_template_path: Đường dẫn prompt template DS
        max_workers: Số threads tối đa
        min_interval: Khoảng thời gian tối thiểu giữa các lần bắt đầu request (giây)
        verbose: Hiển thị logs chi tiết
        max_retries: Số lần retry tối đa khi gặp lỗi
        retry_delay: Delay giữa các lần retry (giây)
        
    Returns:
        List: Danh sách các GeneratedTrueFalseQuestion
    """
    # Set verbose mode
    generator.verbose = verbose
    generator.max_retries = max_retries
    generator.retry_delay = retry_delay
    
    # Chuẩn bị tasks
    tasks = [
        {
            'id': spec.question_code,
            'spec': spec,
            'template_path': prompt_template_path,
            'num_questions': 1  # DS luôn là 1 câu với 4 mệnh đề
        }
        for spec in ds_specs
    ]
    
    # Function xử lý một task
    def process_ds_task(task):
        return generator.generate_true_false_question(
            tf_spec=task['spec'],
            prompt_template_path=task['template_path']
        )
    
    # Xử lý song song
    concurrent_gen = ConcurrentGenerator(
        max_workers=max_workers,
        min_interval=min_interval
    )
    
    results = concurrent_gen.process_batch(
        tasks=tasks,
        process_func=process_ds_task
    )
    
    # Lấy kết quả
    all_questions = []
    for result in results:
        if result.success and result.data:
            all_questions.append(result.data)
    
    return all_questions
