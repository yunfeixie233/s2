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

![Figure 1: a robot reaching for a mug connects physical reality to sensory observations and motion execution. A scatter plot relates Sensorimotor Alignment to success across twelve VLAs.](assets/platonic-robotics.png)

*Left: a robot reaching for a mug gives us two views of one physical interaction, a sensory observation and an executed motion. Sensorimotor Alignment, S², measures whether similar observations in a model's representation correspond to similar demonstrated motions. Right: each point is one VLA. Higher alignment accompanies higher task success in SimplerEnv, a robot simulation benchmark. The correlation across these twelve models is 0.717.*

The Platonic Representation Hypothesis (PRH) argues that as vision and language models scale, their representation spaces converge toward a shared statistical model of reality. The reason is that images and text are both projections of the same underlying world, so better models of either one should end up organizing that world in similar ways.

In this work, we bring PRH to robotics and ask: can physical actions be viewed as another projection of that world, such that more capable embodied models better align their vision and language representations with the structure of motion trajectories?

Our evidence suggests the answer is yes. To test this, we measure how well an embodied model's representation of a sensory input (what it sees and what it is told) aligns with the motor trajectory that should follow. Put simply, if two situations look alike to the model, they should also call for similar motions. We call this measure sensorimotor alignment (S²).

Our first finding is that S² is positively related to downstream robot task success. We test a range of Vision-Language-Action models (VLAs) and World Action Models (WAMs), both in simulation and on real robots. In every setting, models with higher S² achieve higher success rates. This suggests that PRH also holds in robotics: a more capable embodied model is one whose vision and language representations better reflect the structure of physical motion.

S² also explains, at the representation level, several behaviors that prior work has only observed empirically. For example, VLAs often ignore the language instruction and act mainly on what they see. We find that their success tracks the S² of their vision features, not their text features.

More broadly, S² can serve as a low-cost offline proxy for identifying which models are likely to achieve higher task success before closed-loop evaluation. For instance, it can identify promising VLM backbones even before costly VLA fine-tuning.

## Measuring sensorimotor alignment

Camera features and robot trajectories live in different spaces, so we cannot compare them directly. Following PRH, we instead compare their *similarity structures*: does each representation judge the same pairs of episodes to be alike? Each side gives us a kernel $K$, a matrix of pairwise similarities over the same episodes, and S² scores how well the two kernels agree.

We compute S² on a fixed offline dataset $\mathcal{D} = \{e_i\}_{i=1}^N$, such as DROID. Each episode $e_i = (\mathbf{x}_i, \boldsymbol{\tau}_i)$ pairs a sensory input $\mathbf{x}_i$, a camera image and a language instruction, with the trajectory $\boldsymbol{\tau}_i$ that a human teleoperator then executed. Every model is scored against the same recorded motions, so no closed-loop rollouts are needed.

The **sensory kernel** comes from the model. We feed $\mathbf{x}_i$ to the model, extract a feature vector $\mathbf{z}_i$, and compare episodes by cosine similarity, $K^{\mathrm{sensory}}_{ij} = \cos(\mathbf{z}_i, \mathbf{z}_j)$. Because this works for any architecture and layer, we can compare vision features, text features, or features taken at different depths.

The **motor kernel** comes from the robot. Each trajectory records the end-effector position, orientation, and gripper state. The same task can be performed faster or slower, so we compare trajectories with dynamic time warping (DTW), which aligns their timing before measuring distance, $K^{\mathrm{motor}}_{ij} = \mathrm{DTW}(\boldsymbol{\tau}_i, \boldsymbol{\tau}_j)$.

To compare the two kernels, we look at neighborhoods. Take one episode as the query and find its $k$ nearest neighbors under each kernel. The illustration below uses $k = 3$; our experiments use $k = 10$. If the model organizes episodes by the motion they require, the two neighbor sets should largely overlap.

<div class="explainer-slot"></div>

S² aggregates this agreement over every query episode. We use Centered Kernel Nearest-Neighbor Alignment (CKNNA) from PRH, which measures how strongly the two kernels co-vary within these shared neighborhoods:

$$\mathrm{S}^2 = \mathrm{CKNNA}\left(K^{\mathrm{sensory}}, K^{\mathrm{motor}}\right)$$

A high S² means the model places episodes close together when they call for similar motions, not merely when they look or sound alike.

<details class="technical-note">
<summary>Implementation details</summary>

For video datasets, the sensory input uses only the first frame of each episode, matching standard VLA inputs. Trajectories are expressed in the robot base frame. The DTW local cost uses geodesic distance on SO(3) for rotations and native coordinates for positions and gripper state.

</details>

*Based on our research, “Sensorimotor Alignment: A Platonic Proxy for Embodied Policy Success,” by Yunfei Xie, Howard H. Qian, Shiyi Lan, Kaiyu Hang, and Chen Wei.*
