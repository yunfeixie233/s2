<!--
Conventions build.py relies on:
- An optional italic paragraph right after the H1 becomes the subtitle (dek).
- An image paragraph followed by an italic paragraph becomes a numbered figure with that caption; Figure 1 is pulled out as the opening figure.
- Footnotes ([^key]) become margin sidenotes. Write each definition as: [Title](link) (Author et al, Year).
- A table followed by an italic paragraph gets that paragraph as its caption.
- H2 and H3 headings appear in the contents list on the left.
-->

# Sensorimotor Alignment: A Platonic Proxy for Embodied Policy Success

![Figure 1: a robot reaching for a mug connects physical reality to sensory observations and motion execution. A scatter plot relates Sensorimotor Alignment to success rate across twelve VLAs.](assets/platonic-robotics.png)

*Left: a robot reaching for a mug gives us two views of one physical interaction, a sensory observation and an executed motion. Sensorimotor Alignment, S², measures whether similar observations in a model's representation correspond to similar demonstrated motions. Right: each point is one VLA. Higher alignment accompanies higher task success in SimplerEnv, a robot simulation benchmark. The correlation across these twelve models is 0.717.*

The Platonic Representation Hypothesis (PRH)[^prh] argues that as vision and language models scale, their representation spaces converge toward a shared statistical model of reality. The idea is that images and text are different projections of the same underlying world. As models recover that world more faithfully, they begin to agree on which inputs are similar. For example, if a vision model places two images close together in the representation space, a language model tends to place their captions close together too.

In this work, we bring PRH to robotics and ask: can physical actions be viewed as another projection of that world, such that more capable embodied models better align their vision and language representations with the structure of motion trajectories?

**Our evidence suggests the answer is yes.** To test this, we use Sensorimotor Alignment (S²), which measures the overlap between neighborhoods of a model's sensory representations and neighborhoods of end-effector trajectories. Higher alignment means episodes nearby in sensory representation space are also nearby in motor representation space.

Our first finding is that S² is positively related to downstream robot task success. We test a range of Vision-Language-Action models (VLAs) and World Action Models (WAMs) in simulation, as well as policies on real robots. Across these settings, models with higher S² tend to achieve higher task success rates. This pattern provides empirical support for extending PRH to robotics.

S² also explains, at the representation level, several phenomena that prior work has observed only through closed-loop results. For example, VLAs often ignore the language instruction and act mainly on what they see. We find that their task success correlates with the S² of their vision features, not their text features.

In practice, S² can serve as a low-cost offline proxy for identifying which models are likely to achieve higher task success before closed-loop evaluation. For instance, it can identify promising vision-language model (VLM) backbones even before costly VLA fine-tuning.

## Measuring sensorimotor alignment

For each recorded episode, the model's image and text features form its sensory representation, and the end-effector trajectory forms its motor representation. We compute S² by constructing these representations and comparing their neighborhoods, as follows.

**Reference dataset.** To measure cross-modal alignment, we use the DROID[^droid] and BridgeDataV2 datasets, which pair sensory inputs with physical motions. From a dataset, we sample $N$ episodes and compute both representations from each episode. For episode $i$, we randomly sample one image frame and pair it with the task instruction. This image-text pair forms the sensory input $\mathbf{x}_i$.

<div class="alignment-animations" id="dataset-animation">
  <figure class="alignment-animation">
    <img src="assets/01-DROID-to-representations-compact.gif" alt="Animation showing how DROID robot episodes become sensory and motor representations." width="960" height="488" loading="lazy" decoding="async">
    <figcaption class="animation-transcript">We measure sensorimotor alignment on DROID, a large dataset of real robot demonstrations. For each episode, we encode an image frame and the text instruction with the vision and text encoders of a robot foundation model, which forms the sensory representation. The recorded end-effector trajectory forms the motor representation. We use dynamic time warping (DTW) to measure distances between trajectories.</figcaption>
  </figure>
</div>

**Sensory representation.** For each episode $i$, we encode the image frame and text instruction with the vision and text encoders of a robot foundation model, obtaining a sensory embedding $\mathbf{z}_i = f(\mathbf{x}_i) \in \mathbb{R}^{d}$. Here, $f$ applies the vision encoder to the image and the text encoder to the instruction, and we average-pool the output token features into a single $d$-dimensional vector.

**Motor representation.** For the sampled image frame in $\mathbf{x}_i$, we extract end-effector positions, orientations, and gripper states over the next $h$ steps, forming the motor representation $\boldsymbol{\tau}_i \in \mathbb{R}^{h \times 7}$. Each row contains the position coordinates $x,y,z$, roll, pitch, and yaw angles $\phi,\theta,\psi$, and the recorded gripper coordinate $g$. We encode positions as vectors in $\mathbb{R}^3$ and orientation angles as rotations in SO(3), so that distances reflect the geometry of translations and rotations.

**Sensorimotor alignment.** We measure alignment with a mutual nearest-neighbor metric comparing the $k$-nearest-neighbor sets in sensory and motor spaces. Greater overlap indicates stronger alignment between an episode's sensory and motor representations. To identify these neighbors, we use cosine distance in sensory space and dynamic time warping (DTW)[^dtw] in motor space to compare trajectories executed at different speeds. Smaller distances mean closer neighbors:

$$d_{\mathrm{sensory}}(i,j) = 1 - \cos(\mathbf{z}_i, \mathbf{z}_j), \qquad d_{\mathrm{motor}}(i,j) = \mathrm{DTW}(\boldsymbol{\tau}_i, \boldsymbol{\tau}_j)$$

For each episode $i$, we use $d_{\mathrm{sensory}}$ to form the sensory $k$-nearest-neighbor set $\mathcal{N}_{\mathrm{sensory}}(i)$ and $d_{\mathrm{motor}}$ to form the motor $k$-nearest-neighbor set $\mathcal{N}_{\mathrm{motor}}(i)$. We then take the intersection of the two sets, divide its size by $k$, and average over all $N$ episodes:[^prh]

$$m_{\mathrm{NN}} = \frac{1}{Nk}\sum_{i=1}^{N}\left|\mathcal{N}_{\mathrm{sensory}}(i)\cap\mathcal{N}_{\mathrm{motor}}(i)\right|$$

<div class="alignment-animations" id="neighborhood-animation">
  <figure class="alignment-animation">
    <img src="assets/02-measuring-sensorimotor-alignment-compact.gif" alt="Animation explaining how sensory and motor similarity structures are compared to measure sensorimotor alignment." width="960" height="488" loading="lazy" decoding="async">
    <figcaption class="animation-transcript">For each episode, we find its ten closest neighbors in the sensory representation space and its ten closest neighbors in the motor representation space. Higher agreement between the two neighbor sets means higher sensorimotor alignment. We repeat this for every episode to illustrate the neighborhood agreement underlying S².</figcaption>
  </figure>
</div>

Greater overlap indicates that episodes with similar sensory representations also have similar motor trajectories, as the figure below shows for a single query episode.

![A query episode, "place cans into cabinet", with its four nearest neighbors by trajectory similarity (motor neighbors, top row) and by vision-text representation similarity (sensory neighbors, bottom row). Two sensory neighbors also appear among the motor neighbors and are marked with green checks; the other two are marked with red crosses.](assets/s2-worked-example.png)

*Nearest-neighbor overlap illustrates Sensorimotor Alignment (S²). For the query episode (left), the sensory neighbor set (bottom right) contains episodes with similar vision-text features, and the motor neighbor set (top right) contains episodes with similar trajectories. Green checks mark shared neighbors; red crosses mark neighbors found only in the sensory set. Greater overlap indicates that episodes with similar sensory representations also have similar motor trajectories.*

Of the four sensory neighbors shown, two are shared with the motor neighbor set (green checks). The other two are found only in the sensory set (red crosses). One of them even shares the query's instruction, "place cans into cabinet", yet calls for a different motion.

The overlap above illustrates the idea behind S². Our reported score uses a centered, normalized variant of Centered Kernel Nearest-Neighbor Alignment (CKNNA) from PRH,[^prh] with $k = 10$ neighbors; Appendix A.3 of our paper gives the full definition.


## S² Correlates with Robot Task Success Rate

We test our PRH-inspired prediction that models whose sensory representations align more closely with robot trajectories achieve higher task success. For each model, we compare its offline S² with independently measured closed-loop task success. A positive correlation would support both this view of embodiment and the use of S² to identify promising models before closed-loop evaluation.

Below, we establish this positive correlation across three model families and real-robot policies, and show that S² correlates with task success more closely than visual question answering (VQA) scores and video-quality metrics.

### S² Correlates with Task Success Across Model Families

The figure below compares three model families and a separate set of policies evaluated on real robots. Each panel plots S² computed on a reference dataset (x-axis) against downstream manipulation success rate (y-axis). Appendix B of our paper lists the evaluated VLAs, VLMs, world action models (WAMs), and real-robot policies, along with their evaluation protocols and conditions.

![Four scatter plots of Sensorimotor Alignment against success rate, for VLAs, raw VLMs, WAMs, and real-robot policies. Each shows a positive trend, with correlations of 0.717, 0.681, 0.718, and 0.831.](assets/s2-across-families.png)

*Sensorimotor Alignment (S²) correlates with task success across model families and in simulated and real-world evaluations. From left to right, each panel plots offline S² (x-axis) against downstream task success rate (y-axis) for fine-tuned VLAs, raw VLMs, WAMs, and real-robot policies. For raw VLMs, task success is measured after VLA fine-tuning. These correlations support S² as an offline proxy for task success across model families.*

**Vision-language-action models (VLAs).** We test 12 VLAs against their SimplerEnv[^simplerenv] success rates. The Pearson correlation r = +0.717 is strong. Thus, models with higher sensorimotor alignment tend to achieve higher task success rates.

**Vision-language models (VLMs).** We ask whether S² computed on a raw VLM, before any robot fine-tuning, correlates with the task success of the VLA that is later fine-tuned from that backbone. We compute S² for 8 raw VLM backbones from VLM4VLA[^vlm4vla] and compare it with the SimplerEnv[^simplerenv] success rate of the VLAs that VLM4VLA fine-tunes from them. We find a strong correlation with downstream VLA success rate: r = +0.681. This result demonstrates the practical utility of S²: it can identify promising VLM backbones even before costly VLA fine-tuning.

**World action models (WAMs).** Finally, we test WAMs, which build on video generators rather than VLMs. We compute S² for 6 WAMs on the bimanual ALOHA dataset[^aloha] and compare it with their success rates on RoboTwin 2.0[^robotwin]. For WAMs, the sensory representation is the video-generator latent used for action decoding, and all 6 models share the same ALOHA trajectories and S² settings. Across these 6 models, S² shows a strong correlation with task success, r = +0.718.

**Real-robot policies.** We test whether the correlation observed in simulation extends to real robots. Because real-world success rates depend on many factors, such as the task set, robot, cameras, and protocol, we take all success rates from a single unified setting: the physical-robot results that MolmoB0T[^molmobot] reports for 5 policies on 40 tasks. We then compute S² for their public checkpoints on the same DROID reference dataset. Across these 5 policies, S² shows a strong correlation with real-robot task success, r = +0.831.

We further validate that S² correlates with downstream task success for frozen vision backbones under low-data behavior cloning and visual-reward learning, as shown in Appendix B.6 of our paper.

### S² Correlates with Task Success More Closely Than Alternative Metrics

Prior work asks whether offline scores correlate with downstream task performance. VLM4VLA[^vlm4vla] examines the correlation between VQA benchmark scores and the performance of the resulting VLA policies, finding weak or even negative correlations. For video models, Tian et al.[^tian] find that the quality of predicted video agrees inconsistently with downstream performance across tasks. A common limitation is that these metrics measure language understanding or pixel-level video quality, neither of which is grounded in the physical motion the robot must execute. S² addresses this gap by comparing the nearest-neighbor sets of sensory embeddings and motor trajectories. As we show below, S² correlates more strongly with task success rate than any VQA or video-quality metric we evaluate.

**S² correlates with VLA success rate where VQA scores do not.** We compare S² with aggregate VQA scores as offline proxies, using the same 8 raw VLM backbones and evaluation setting as in the VLM comparison above. We find that VQA scores show virtually no correlation with VLA success rate, at r = −0.154 (figure below, right). S², by contrast, correlates strongly, at r = +0.681 (figure below, left).

![Two scatter plots for eight raw VLMs. Left: Sensorimotor Alignment against SimplerEnv success rate, with correlation 0.681. Right: average VQA score against the same success rates, with correlation −0.154.](assets/s2-vs-vqa.png)

*Sensorimotor Alignment (S²) correlates with VLA success rate where VQA scores do not. Across 8 raw VLMs,[^vlm4vla] S² (left) correlates strongly with SimplerEnv task success after fine-tuning into VLAs, whereas VQA scores (right) show virtually no correlation. The left panel repeats the raw-VLM result from the figure above for comparison.*

**S² correlates with WAM success rate more closely than video-quality metrics.** We compare S² with standard video-quality metrics (FID[^fid], SSIM[^ssim], and PSNR[^psnr]) on 3 of the WAMs, Motus[^motus], LingBot-VA[^lingbot], and Vidar[^vidar], evaluated on RoboTwin. We find that video-quality metrics correlate weakly with task success: SSIM reaches only r = +0.558 and PSNR only r = +0.468, while FID even runs backwards, at r = +0.680, where lower video quality goes with higher success (figure below). By contrast, S² on ALOHA correlates more strongly, at r = +0.999.

![Four scatter plots of RoboTwin success rate for three WAMs against Sensorimotor Alignment, SSIM, PSNR, and FID. Only Sensorimotor Alignment orders the three models by success rate.](assets/s2-vs-video-quality.png)

*Sensorimotor Alignment (S²) correlates with WAM success rate more closely than video-quality metrics. For 3 WAMs evaluated on RoboTwin, video-quality metrics (SSIM, PSNR, FID) show no significant correlations with task success. In contrast, only S² correctly recovers the success-rate ordering. Only 3 of the 6 WAMs are compared because the others do not generate future video during closed-loop task evaluation.*

<div id="robustness-and-reference-data"></div>

### S² Is Robust to Evaluation Choices

The positive correlation between S² and task success is robust to the evaluation choices tested in the paper, including the reference dataset, trajectory horizon, and metric implementation. See Section 3.3 and Appendix C for the full results and details.

## Representation-Level Explanations with S²

Several phenomena reported for VLAs and WAMs rest only on closed-loop results and still lack a representation-level explanation. Because S² correlates with task success, as shown above, we use it to explain each of these phenomena, as summarized below:

- **[Modality dominance](#what-carries-the-correlation-vision-text-or-both)**: prior work observes that VLAs often struggle with instruction grounding: they act on what the scene visually suggests rather than on what the language instruction asks[^liberoplus][^liberocf][^igar]. We explain that after VLA fine-tuning, task success is associated with vision-feature S² but not text-feature S², indicating that fine-tuned VLAs draw on what they see, not on the instruction, to produce the right motion.
- **[Frozen encoders](#freezing-vision-encoders-limits-s²-gain)**: prior work observes that freezing the vision encoder during VLA fine-tuning degrades downstream task performance[^vlm4vla]. We explain that freezing also prevents the S² gain from end-to-end fine-tuning, indicating that VLAs gain performance by bringing their sensory representation closer to the motor representation.
- **[Iterative denoising](#features-at-early-denoising-steps-already-carry-strong-sensorimotor-alignment)**: prior work observes that WAMs can skip iterative video denoising at test time, decoding actions without generating future video, with little loss in task success[^fastwam]. We explain that the S² of WAM features is already high at the earliest denoising step and changes little afterwards, indicating that the first denoising steps already yield features aligned closely enough with robot trajectories to act on.
- **[Mid-depth blocks](#mid-depth-blocks-carry-the-strongest-sensorimotor-alignment)**: prior work observes that mid-depth blocks of video diffusion transformers matter most for semantic reasoning[^demystifying]. We explain that these blocks also carry the strongest S², indicating that the layers that reason about video semantics are also the layers most aligned with robot motion.

### What Carries the Correlation: Vision, Text, or Both?

VLAs often struggle with instruction grounding[^liberoplus][^liberocf][^igar]. We use S² to explain this at the representation level, asking which modality the correlation with task success depends on: vision, text, or both. In the figure below, we compute S² separately for each modality. We take the VLM output tokens read by the action head and form *vision features* from the image tokens, *text features* from the instruction tokens, and *joint vision-text features* from all tokens.

![A two-by-three grid of scatter plots relating Sensorimotor Alignment to SimplerEnv success rate. Top row, twelve fine-tuned VLAs: vision-only 0.694, text-only 0.237, vision plus text 0.699. Bottom row, eight raw VLMs: vision-only 0.425, text-only 0.501, vision plus text 0.681.](assets/s2-what-carries.png)

*Fine-tuned VLAs rely mainly on visual rather than language representations to produce the right motion. We correlate Sensorimotor Alignment (S²) from vision, text, and joint vision-text features (left to right) with SimplerEnv task success rate. **Top:** For fine-tuned VLAs, vision and joint features yield similarly strong correlations, while text features yield a weak correlation. **Bottom:** For raw VLMs, joint-feature S² correlates with task success after VLA fine-tuning, while neither modality alone reaches significance.*

**Fine-tuned VLAs rely mainly on visual rather than language representations to produce the right motion.** In the 12 fine-tuned VLAs, S² from vision features correlates with SimplerEnv success rate at r = +0.694, nearly matching the joint vision-text features at r = +0.699, whereas text features show no significant correlation at r = +0.237. The raw VLMs reverse this pattern: before fine-tuning, text features correlate at r = +0.501, more strongly than vision features at r = +0.425, and joint vision-text features correlate most strongly at r = +0.681.

We infer that, after fine-tuning, VLAs produce their motion mainly from visual rather than language representations, which explains their weak instruction grounding at the representation level. Appendix D.1 of our paper reports per-model S² at all feature positions.

### Freezing Vision Encoders Limits S² Gain

VLM4VLA[^vlm4vla] reports that VLAs perform substantially worse when their vision encoder stays frozen during fine-tuning. We use S² to explain this drop at the representation level, testing whether freezing also prevents the sensorimotor-alignment gain from end-to-end fine-tuning.

In the figure below, we compare 2 VLAs that follow the same VLM4VLA[^vlm4vla] recipe and differ only in whether the vision encoder is trained or kept frozen. For each, we compute S² and measure SimplerEnv success rate. Freezing the encoder reduces S² by 41% and the downstream task success rate by 40%, with more detail in Appendix D.2 of our paper. These results suggest that end-to-end fine-tuning improves performance by aligning the sensory representation more closely with the motor representation.

![Bar charts comparing unfrozen and frozen vision-encoder fine-tuning. Sensorimotor Alignment drops from 0.0245 to 0.0144, and SimplerEnv success rate drops from 50.00 percent to 30.21 percent.](assets/s2-freeze-vs-unfreeze.png)

*Freezing the vision encoder reduces both Sensorimotor Alignment (S²) and task success rate. For Qwen2.5-VL-3B VLAs fine-tuned on BridgeDataV2, we compare end-to-end training with a frozen vision encoder. Freezing lowers both S² from joint vision-text features (top) and SimplerEnv task success rate (bottom), linking lower task success to weaker sensorimotor alignment. Trajectory horizon h = 7.*

### Features at Early Denoising Steps Already Carry Strong Sensorimotor Alignment

Most WAMs generate future video through iterative denoising and decode actions from the resulting latents. Fast-WAM[^fastwam] shows that WAMs can skip this video generation and decode actions directly, with little loss in task success. We examine the representation-level reason: whether features at the earliest denoising steps already align with robot trajectories.

We measure S² for 3 WAMs[^motus][^lingbot][^vidar] on RoboTwin[^robotwin], as shown in the figure below. We compute S² from each model's latent features at 5 positions in its native denoising schedule, from 0% to 100%, not at matched noise levels. S² is already high at the earliest step and remains nearly flat, varying by about 6% at most from its initial value across the 3 models. We infer that early-step features are already sufficiently aligned with robot trajectories to generate actions. Because S² correlates with WAM success rate, as shown above, this result explains why skipping iterative video denoising barely lowers task success.

![Line plot of Sensorimotor Alignment for three WAMs at five points of the denoising schedule, from 0 to 100 percent. All three lines stay nearly flat.](assets/s2-denoising.png)

*Sensorimotor Alignment (S²) is already high at early denoising steps. For 3 WAMs, S² remains nearly flat across denoising, suggesting that early-step features are already aligned with robot trajectories.*

### Mid-Depth Blocks Carry the Strongest Sensorimotor Alignment

Prior analysis of Chain-of-Steps[^demystifying] shows that mid-depth layers in Video Diffusion Transformers are especially important for semantic reasoning over objects and interactions. We ask whether the layers with the highest S² also lie in this mid-depth range.

In the figure below, we compute S² at different depths of 3 WAMs[^motus][^lingbot][^vidar] on RoboTwin. All 3 share a 30-block video backbone, and we extract features from Blocks 0, 7, 14, 21, and 29. Block 14 yields the highest S² in every model. This peak falls in the mid-depth range that Chain-of-Steps[^demystifying] identifies as semantically important, suggesting that the layers handling video semantic reasoning align most closely with robot motion. Details are in Appendix D.3 of our paper.

![Line plot of Sensorimotor Alignment at backbone Blocks 0, 7, 14, 21, and 29 for three WAMs. Each line peaks at Block 14.](assets/s2-layerwise.png)

*Schedule-averaged Sensorimotor Alignment (S²) peaks at Block 14 in all 3 WAMs, indicating that mid-depth blocks carry the strongest sensorimotor alignment.*

<div id="using-s²"></div>

## Conclusion

Our results support a PRH-inspired view of embodiment: more capable models tend to align their sensory representations more closely with robot motion. S² makes this relationship measurable offline and helps identify promising models and VLM backbones before costly fine-tuning or closed-loop evaluation. It also helps diagnose how model and training choices relate to embodied performance.

**Limitations.** These findings are correlations across a limited set of model families, benchmarks, and training recipes, with few models per comparison and one real-robot setting. Models with similar S² can still differ in task success, so closed-loop evaluation remains the final step in model selection. Whether training directly for higher S² improves robot task success remains an open question.

## Citation

Please cite this work as:

```
Xie, Yunfei, Howard H. Qian, Shiyi Lan, Kaiyu Hang, and Chen Wei. "Sensorimotor Alignment: A Platonic Proxy for Embodied Policy Success." 2026.
```

Or use the BibTeX citation:

```
@misc{xie2026sensorimotor,
  title  = {Sensorimotor Alignment: A Platonic Proxy for Embodied Policy Success},
  author = {Xie, Yunfei and Qian, Howard H. and Lan, Shiyi and Hang, Kaiyu and Wei, Chen},
  year   = {2026}
}
```

[^prh]: [The Platonic Representation Hypothesis](https://arxiv.org/abs/2405.07987) (Huh et al, 2024)
[^droid]: [DROID: A Large-Scale In-the-Wild Robot Manipulation Dataset](https://arxiv.org/abs/2403.12945) (Khazatsky et al, 2024)
[^dtw]: [Dynamic Programming Algorithm Optimization for Spoken Word Recognition](https://doi.org/10.1109/TASSP.1978.1163055) (Sakoe and Chiba, 1978)
[^simplerenv]: [Evaluating Real-World Robot Manipulation Policies in Simulation](https://arxiv.org/abs/2405.05941) (Li et al, 2024)
[^vlm4vla]: [VLM4VLA: Revisiting Vision-Language-Models in Vision-Language-Action Models](https://arxiv.org/abs/2601.03309) (Zhang et al, 2026)
[^aloha]: [Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware](https://arxiv.org/abs/2304.13705) (Zhao et al, 2023)
[^robotwin]: [RoboTwin: Dual-Arm Robot Benchmark with Generative Digital Twins](https://arxiv.org/abs/2504.13059) (Mu et al, 2025)
[^molmobot]: [MolmoB0T: Large-Scale Simulation Enables Zero-Shot Manipulation](https://arxiv.org/abs/2603.16861) (Deshpande et al, 2026)
[^tian]: [A Control-Centric Benchmark for Video Prediction](https://arxiv.org/abs/2304.13723) (Tian et al, 2023)
[^fid]: [GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium](https://arxiv.org/abs/1706.08500) (Heusel et al, 2017)
[^ssim]: [Image Quality Assessment: From Error Visibility to Structural Similarity](https://doi.org/10.1109/TIP.2003.819861) (Wang et al, 2004)
[^psnr]: [Image Quality Metrics: PSNR vs. SSIM](https://doi.org/10.1109/ICPR.2010.579) (Horé and Ziou, 2010)
[^liberoplus]: [LIBERO-Plus: A Progressive Robustness Benchmark for Visual-Language-Action Models](https://arxiv.org/abs/2510.13626) (Fei et al, 2026)
[^liberocf]: [When Vision Overrides Language: Evaluating and Mitigating Counterfactual Failures in VLAs](https://arxiv.org/abs/2602.17659) (Fang et al, 2026)
[^igar]: [Restoring Linguistic Grounding in VLA Models via Train-Free Attention Recalibration](https://arxiv.org/abs/2603.06001) (Zhang et al, 2026)
[^fastwam]: [Fast-WAM: Do World Action Models Need Test-time Future Imagination?](https://arxiv.org/abs/2603.16666) (Yuan et al, 2026)
[^demystifying]: [Demystifying Video Reasoning](https://arxiv.org/abs/2603.16870) (Wang et al, 2026)
[^motus]: [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) (Bi et al, 2026)
[^lingbot]: [Causal World Modeling for Robot Control](https://arxiv.org/abs/2601.21998) (Li et al, 2026)
[^vidar]: [Vidar: Embodied Video Diffusion Model for Generalist Manipulation](https://arxiv.org/abs/2507.12898) (Feng et al, 2025)
