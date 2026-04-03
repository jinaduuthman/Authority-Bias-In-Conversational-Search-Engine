"""
Generate experiment query sets: for each topic, create queries
paired with 10-paper candidate sets drawn from diverse tiers.

Reads:  data/experiment_conditions.json
Writes: data/experiment_sets.json
"""

import json
import os
import random

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONDITIONS_FILE = os.path.join(BASE_DIR, "data", "experiment_conditions.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "experiment_sets.json")

CANDIDATE_SET_SIZE = 10

# Queries per topic — each tests a different angle within the topic
TOPIC_QUERIES = {
    "Knowledge Distillation": [
        "What are effective knowledge distillation techniques for large language models?",
        "How can I improve student model performance in neural network distillation?",
        "Which distillation approaches work best for vision transformers?",
        "How do feature-based and response-based distillation compare?",
        "What are efficient methods for compressing BERT-sized models through distillation?",
        "How can knowledge distillation preserve reasoning capabilities in smaller models?",
        "What role does temperature scaling play in knowledge distillation effectiveness?",
        "How do self-distillation methods compare to traditional teacher-student frameworks?",
        "What distillation strategies work best for multi-task language models?",
        "How can intermediate layer matching improve distillation outcomes?",
    ],
    "Prompt Engineering": [
        "What are the most effective prompt engineering strategies for reasoning tasks?",
        "How does chain-of-thought prompting improve language model performance?",
        "What techniques exist for automatic prompt optimization?",
        "How do few-shot prompting methods compare across different LLMs?",
        "What are best practices for designing prompts for code generation?",
        "How does instruction tuning relate to prompt engineering effectiveness?",
        "What methods improve prompt robustness across different model sizes?",
        "How can retrieval-augmented prompting enhance factual accuracy?",
        "What role does prompt formatting play in multi-step reasoning?",
        "How do self-consistency prompting methods reduce output variance?",
    ],
    "LLM Alignment": [
        "How does RLHF improve language model alignment with human preferences?",
        "What are alternatives to RLHF for aligning large language models?",
        "How can we evaluate whether a language model is properly aligned?",
        "What techniques reduce harmful outputs in conversational AI?",
        "How does direct preference optimization compare to traditional RLHF?",
        "What methods ensure alignment stability during continued training?",
        "How can constitutional AI principles guide language model alignment?",
        "What role does reward model quality play in RLHF effectiveness?",
        "How do alignment techniques handle conflicting human preferences?",
        "What approaches scale alignment methods to very large language models?",
    ],
    "Text Summarization": [
        "What are state-of-the-art methods for abstractive text summarization?",
        "How can we improve faithfulness in neural summarization models?",
        "What approaches work best for long document summarization?",
        "How do extractive and abstractive summarization methods compare?",
        "What techniques handle multi-document summarization effectively?",
        "How can summarization models better preserve factual consistency?",
        "What methods improve summarization for domain-specific technical texts?",
        "How do controllable summarization approaches adjust output length and style?",
        "What techniques handle cross-lingual summarization effectively?",
        "How can evaluation metrics better capture summarization quality?",
    ],
    "Machine Translation": [
        "What are the best approaches for low-resource neural machine translation?",
        "How do multilingual translation models handle language pairs with limited data?",
        "What techniques improve translation quality for morphologically rich languages?",
        "How does document-level context improve machine translation?",
        "What are effective methods for simultaneous speech translation?",
        "How can back-translation improve neural machine translation quality?",
        "What approaches handle code-switching in machine translation?",
        "How do adapter-based methods improve multilingual translation efficiency?",
        "What techniques improve translation of domain-specific terminology?",
        "How can quality estimation predict machine translation errors without references?",
    ],
    "Named Entity Recognition": [
        "What are the best methods for few-shot named entity recognition?",
        "How can NER systems handle nested and overlapping entities?",
        "What approaches work well for biomedical named entity recognition?",
        "How do cross-lingual NER methods transfer across languages?",
        "What techniques improve NER on noisy social media text?",
        "How can prompt-based approaches improve named entity recognition?",
        "What methods handle emerging and unseen entity types in NER?",
        "How do span-based NER models compare to sequence labeling approaches?",
        "What techniques improve NER in low-resource languages?",
        "How can active learning reduce annotation cost for NER systems?",
    ],
    "Sentiment Analysis": [
        "What are the best deep learning approaches for aspect-based sentiment analysis?",
        "How can multimodal data improve sentiment classification?",
        "What methods handle implicit sentiment and sarcasm detection?",
        "How do transformer-based models compare for fine-grained sentiment analysis?",
        "What techniques work best for cross-domain sentiment adaptation?",
        "How can graph neural networks capture opinion dependencies in sentiment analysis?",
        "What approaches handle sentiment analysis in code-mixed languages?",
        "How do prompt-based methods perform for zero-shot sentiment classification?",
        "What techniques improve sentiment analysis for product reviews with conflicting opinions?",
        "How can contrastive learning improve sentiment representation?",
    ],
    "Question Answering": [
        "What are the best retrieval-augmented approaches for open-domain question answering?",
        "How do multi-hop reasoning methods improve complex question answering?",
        "What approaches work best for visual question answering?",
        "How can question answering systems handle unanswerable questions?",
        "What techniques improve factual consistency in generative QA?",
        "How do table-based question answering methods handle structured data?",
        "What approaches improve conversational question answering over multiple turns?",
        "How can knowledge graphs enhance question answering accuracy?",
        "What methods handle ambiguous questions requiring clarification?",
        "How do dense passage retrieval methods improve QA pipeline performance?",
    ],
    "Federated Learning": [
        "How can federated learning handle non-IID data distributions across clients?",
        "What are the best communication-efficient federated learning algorithms?",
        "How can we ensure privacy guarantees in federated deep learning?",
        "What methods address client heterogeneity in federated settings?",
        "How does federated learning apply to natural language processing tasks?",
        "What techniques improve convergence speed in federated optimization?",
        "How can personalized federated learning adapt to individual client needs?",
        "What defenses exist against Byzantine attacks in federated learning?",
        "How do federated learning methods handle client dropout and stragglers?",
        "What approaches combine differential privacy with federated learning?",
    ],
    "Meta-Learning": [
        "What are effective meta-learning approaches for few-shot image classification?",
        "How does MAML compare to other gradient-based meta-learning methods?",
        "What techniques improve meta-learning generalization to out-of-distribution tasks?",
        "How can meta-learning be applied to reinforcement learning?",
        "What are the best task augmentation strategies for meta-learning?",
        "How do metric-based meta-learning methods compare to optimization-based ones?",
        "What approaches improve meta-learning with limited task diversity?",
        "How can meta-learning handle cross-domain few-shot transfer?",
        "What techniques make meta-learning scalable to large model architectures?",
        "How do task-agnostic meta-learning representations benefit downstream tasks?",
    ],
    "Reinforcement Learning": [
        "What are the most sample-efficient deep reinforcement learning algorithms?",
        "How do offline reinforcement learning methods learn from static datasets?",
        "What approaches work best for multi-agent reinforcement learning?",
        "How can reward shaping improve reinforcement learning convergence?",
        "What methods handle partial observability in deep RL?",
        "How do model-based reinforcement learning methods improve sample efficiency?",
        "What techniques transfer reinforcement learning policies across environments?",
        "How can hierarchical reinforcement learning decompose complex tasks?",
        "What approaches handle sparse reward signals in deep RL?",
        "How do safe reinforcement learning methods enforce constraints during training?",
    ],
    "Transfer Learning": [
        "What are the best strategies for domain adaptation in deep learning?",
        "How does pre-training on large datasets improve transfer learning?",
        "What techniques handle negative transfer between domains?",
        "How can transfer learning be applied with limited target domain data?",
        "What methods work best for cross-lingual transfer in NLP?",
        "How do adapter modules enable parameter-efficient transfer learning?",
        "What approaches handle domain shift in visual transfer learning?",
        "How can multi-source domain adaptation improve transfer robustness?",
        "What techniques measure transferability between source and target tasks?",
        "How does continual pre-training improve domain-specific transfer?",
    ],
    "Self-Supervised Learning": [
        "What are the best contrastive learning methods for visual representation?",
        "How does masked image modeling compare to contrastive self-supervised learning?",
        "What self-supervised approaches work best for speech and audio?",
        "How can self-supervised pre-training improve downstream NLP tasks?",
        "What techniques prevent representation collapse in self-supervised learning?",
        "How do joint-embedding methods compare to generative self-supervised approaches?",
        "What role does data augmentation play in contrastive self-supervised learning?",
        "How can self-supervised learning handle multi-modal data effectively?",
        "What approaches improve self-supervised learning on small datasets?",
        "How do self-supervised vision transformers compare to supervised ones?",
    ],
    "Graph Neural Networks": [
        "What are the best graph neural network architectures for node classification?",
        "How do graph transformers improve over standard message-passing GNNs?",
        "What techniques address over-smoothing in deep graph neural networks?",
        "How can GNNs handle heterogeneous graphs with different node types?",
        "What methods scale graph neural networks to large graphs?",
        "How do spectral and spatial graph convolution methods compare?",
        "What approaches improve graph neural network expressiveness beyond WL test?",
        "How can GNNs incorporate temporal dynamics in dynamic graphs?",
        "What pre-training strategies improve GNN performance on downstream tasks?",
        "How do graph pooling methods affect GNN performance on graph classification?",
    ],
    "Generative Adversarial Networks": [
        "What are the best techniques for stabilizing GAN training?",
        "How do conditional GANs improve image-to-image translation?",
        "What GAN architectures produce the highest quality image synthesis?",
        "How can mode collapse be prevented in generative adversarial training?",
        "What methods improve text-to-image generation with GANs?",
        "How do evaluation metrics like FID and IS measure GAN quality?",
        "What approaches enable GANs to generate high-resolution images?",
        "How can GANs be applied to data augmentation for limited datasets?",
        "What techniques improve semantic editing with GAN latent spaces?",
        "How do 3D-aware GANs generate view-consistent images?",
    ],
    "Object Detection": [
        "What are the best real-time object detection architectures?",
        "How do transformer-based detectors compare to CNN-based approaches?",
        "What methods improve small object detection accuracy?",
        "How can object detection work with limited labeled training data?",
        "What techniques improve 3D object detection from point clouds?",
        "How do anchor-free detectors compare to anchor-based approaches?",
        "What methods improve object detection under domain shift?",
        "How can multi-scale feature fusion improve detection performance?",
        "What approaches handle occluded objects in dense detection scenes?",
        "How do knowledge distillation methods compress object detection models?",
    ],
    "Image Segmentation": [
        "What are state-of-the-art methods for semantic segmentation?",
        "How do instance segmentation approaches handle overlapping objects?",
        "What techniques improve medical image segmentation accuracy?",
        "How can segmentation models generalize across different domains?",
        "What methods work best for interactive and prompted segmentation?",
        "How do panoptic segmentation methods unify semantic and instance segmentation?",
        "What approaches improve segmentation with limited pixel-level annotations?",
        "How can attention mechanisms improve segmentation boundary quality?",
        "What techniques handle class imbalance in semantic segmentation?",
        "How do foundation models like SAM change the segmentation landscape?",
    ],
    "Image Generation": [
        "How do diffusion models compare to GANs for image generation?",
        "What techniques improve text-to-image generation fidelity?",
        "How can image generation models achieve better controllability?",
        "What methods reduce sampling time in diffusion-based generation?",
        "How do latent diffusion models improve generation efficiency?",
        "What approaches improve consistency in generated image compositions?",
        "How can classifier-free guidance improve conditional generation quality?",
        "What techniques enable high-resolution image generation with limited compute?",
        "How do score-based models relate to denoising diffusion approaches?",
        "What methods improve temporal consistency in video generation models?",
    ],
    "Explainable AI": [
        "What are the most reliable post-hoc explanation methods for deep learning?",
        "How can attention mechanisms serve as explanations in neural networks?",
        "What techniques produce faithful explanations for black-box models?",
        "How do concept-based explanations compare to feature attribution methods?",
        "What evaluation metrics best measure explanation quality?",
        "How can counterfactual explanations improve model interpretability?",
        "What methods provide global explanations for complex neural networks?",
        "How do explanation methods differ between NLP and computer vision models?",
        "What approaches make explanation methods computationally efficient?",
        "How can user studies evaluate the practical utility of AI explanations?",
    ],
    "Fairness in Machine Learning": [
        "What methods effectively mitigate bias in machine learning classifiers?",
        "How can fairness constraints be incorporated during model training?",
        "What techniques detect and measure bias in NLP models?",
        "How do fairness interventions affect model accuracy tradeoffs?",
        "What approaches ensure group fairness in recommendation systems?",
        "How can intersectional fairness be addressed in ML systems?",
        "What methods audit pre-trained language models for social bias?",
        "How do causal approaches to fairness differ from statistical ones?",
        "What techniques ensure fairness in automated hiring systems?",
        "How can synthetic data generation help mitigate dataset bias?",
    ],
    "Adversarial Robustness": [
        "What are the most effective adversarial training methods for deep learning?",
        "How can certified defenses guarantee robustness against perturbations?",
        "What techniques improve adversarial robustness without sacrificing accuracy?",
        "How do adversarial attacks transfer between different model architectures?",
        "What methods detect adversarial examples at inference time?",
        "How does adversarial robustness relate to model generalization?",
        "What approaches defend against patch-based adversarial attacks?",
        "How can ensemble methods improve adversarial robustness?",
        "What techniques make adversarial training more computationally efficient?",
        "How do adversarial attacks affect large language models specifically?",
    ],
    "Recommender Systems": [
        "What are the best deep learning architectures for collaborative filtering?",
        "How do sequential recommendation models capture user behavior patterns?",
        "What techniques address the cold-start problem in recommendation?",
        "How can knowledge graphs improve recommendation accuracy?",
        "What methods handle multi-objective optimization in recommender systems?",
        "How do conversational recommender systems elicit user preferences?",
        "What approaches improve recommendation diversity beyond accuracy?",
        "How can graph neural networks model user-item interactions for recommendation?",
        "What techniques handle implicit feedback in recommender systems?",
        "How do cross-domain recommendation methods transfer knowledge between domains?",
    ],
    "Time Series Forecasting": [
        "How do transformer-based models perform on time series forecasting?",
        "What methods work best for multivariate time series prediction?",
        "How can deep learning models handle irregularly sampled time series?",
        "What techniques improve long-horizon time series forecasting?",
        "How do foundation models compare to specialized time series methods?",
        "What approaches handle non-stationary time series distributions?",
        "How can probabilistic forecasting quantify prediction uncertainty?",
        "What methods improve time series forecasting with external covariates?",
        "How do temporal convolutional networks compare to recurrent approaches?",
        "What techniques improve time series anomaly detection accuracy?",
    ],
    "Neural Architecture Search": [
        "What are the most efficient neural architecture search methods?",
        "How does differentiable NAS compare to evolutionary approaches?",
        "What techniques make NAS practical for large-scale models?",
        "How can hardware constraints be incorporated into architecture search?",
        "What NAS methods work best for transformer architecture discovery?",
        "How do one-shot NAS methods reduce search cost?",
        "What approaches improve NAS transferability across different tasks?",
        "How can multi-objective NAS balance accuracy and efficiency?",
        "What role do predictor-based methods play in accelerating NAS?",
        "How do NAS-designed architectures compare to manually designed ones?",
    ],
    "Attention Mechanisms": [
        "What are the most efficient alternatives to standard self-attention?",
        "How do linear attention mechanisms compare to softmax attention?",
        "What techniques reduce the quadratic complexity of transformer attention?",
        "How can multi-head attention be made more interpretable?",
        "What attention variants work best for long-sequence modeling?",
        "How do sparse attention patterns affect transformer performance?",
        "What role does relative position encoding play in attention quality?",
        "How can cross-attention improve multi-modal fusion?",
        "What approaches combine local and global attention effectively?",
        "How do flash attention implementations improve computational efficiency?",
    ],
}


def select_candidate_set(papers, size=CANDIDATE_SET_SIZE):
    """Select a diverse set of papers across tiers."""
    by_tier = {}
    for p in papers:
        tier = p.get("tier", "unknown")
        by_tier.setdefault(tier, []).append(p)

    # Target distribution: 3 top, 3 mid, 2 low, 2 emerging
    targets = {"top": 3, "mid": 3, "low": 2, "emerging": 2}
    selected = []
    used_ids = set()

    for tier, count in targets.items():
        pool = by_tier.get(tier, [])
        random.shuffle(pool)
        for p in pool:
            if len(selected) >= size:
                break
            if p["paper_id"] not in used_ids:
                used_ids.add(p["paper_id"])
                selected.append(p)
                count -= 1
                if count <= 0:
                    break

    # Fill remaining from any tier
    if len(selected) < size:
        remaining = [p for p in papers if p["paper_id"] not in used_ids]
        random.shuffle(remaining)
        for p in remaining:
            if len(selected) >= size:
                break
            selected.append(p)

    random.shuffle(selected)
    return selected


def main():
    with open(CONDITIONS_FILE, "r") as f:
        conditions = json.load(f)

    experiment_sets = {}
    total_sets = 0

    for topic, topic_data in conditions.items():
        queries = TOPIC_QUERIES.get(topic, [])
        if not queries:
            print(f"  WARNING: No queries defined for {topic}, skipping.")
            continue

        original_papers = topic_data["original"]
        flipped_papers = topic_data["flipped"]
        boosted_papers = topic_data["boosted"]

        topic_sets = []

        for q_idx, query in enumerate(queries):
            # Select 10 papers from ORIGINAL (determines which papers are used)
            candidate_set = select_candidate_set(original_papers)
            selected_ids = [p["paper_id"] for p in candidate_set]

            # Pull the same papers from flipped and boosted conditions
            flipped_set = [p for p in flipped_papers if p["paper_id"] in selected_ids]
            boosted_set = [p for p in boosted_papers if p["paper_id"] in selected_ids]

            # Maintain same ordering across conditions
            id_order = {pid: i for i, pid in enumerate(selected_ids)}
            flipped_set.sort(key=lambda p: id_order.get(p["paper_id"], 99))
            boosted_set.sort(key=lambda p: id_order.get(p["paper_id"], 99))

            query_set = {
                "query_id": f"{topic.lower().replace(' ', '_')}_q{q_idx + 1}",
                "topic": topic,
                "query": query,
                "candidates": {
                    "original": candidate_set,
                    "flipped": flipped_set,
                    "boosted": boosted_set,
                },
            }
            topic_sets.append(query_set)
            total_sets += 1

        experiment_sets[topic] = topic_sets
        print(f"  {topic}: {len(topic_sets)} query sets × 3 conditions")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(experiment_sets, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Total query sets: {total_sets}")
    print(f"Total experiment runs per model per variant: {total_sets * 3}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
