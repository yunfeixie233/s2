<!--
Conventions build.py relies on:
- The first paragraph after the H1 becomes the subtitle (dek).
- An image paragraph followed by an italic paragraph becomes a numbered figure with that caption; Figure 1 is pulled out as the opening figure.
- <details class="technical-note"> blocks are collapsible asides and are excluded from the read-time estimate.
- A table followed by an italic paragraph gets that paragraph as its caption.
- The last paragraph becomes the paper note.
-->

# Title

*Subtitle.*

The Platonic Representation Hypothesis (PRH) argues that as vision and language models scale, their representation spaces converge toward a shared statistical model of reality. The reason is that images and text are both projections of the same underlying world, so better models of either one should end up organizing that world in similar ways.

In this work, we bring PRH to robotics and ask: can physical actions be viewed as another projection of that world, such that more capable embodied models better align their vision and language representations with the structure of motion trajectories?

Our evidence suggests the answer is yes. To test this, we measure how well an embodied model's representation of a sensory input (what it sees and what it is told) aligns with the motor trajectory that should follow. Put simply, if two situations look alike to the model, they should also call for similar motions. We call this measure sensorimotor alignment (S²).

Our first finding is that S² is positively related to downstream robot task success. We test a range of Vision-Language-Action models (VLAs) and World Action Models (WAMs), both in simulation and on real robots. In every setting, models with higher S² achieve higher success rates. This suggests that PRH also holds in robotics: a more capable embodied model is one whose vision and language representations better reflect the structure of physical motion.

S² also explains, at the representation level, several behaviors that prior work has only observed empirically. For example, VLAs often ignore the language instruction and act mainly on what they see. We find that their success tracks the S² of their vision features, not their text features.

More broadly, S² can serve as a low-cost offline proxy for identifying which models are likely to achieve higher task success before closed-loop evaluation. For instance, it can identify promising VLM backbones even before costly VLA fine-tuning.

## Section

Text.

*Based on our research, “Sensorimotor Alignment: A Platonic Proxy for Embodied Policy Success,” by Yunfei Xie, Howard H. Qian, Shiyi Lan, Kaiyu Hang, and Chen Wei.*
