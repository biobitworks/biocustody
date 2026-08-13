# 90-Second Demo Script Draft

Bio-Delta-G asks a narrow, testable question: did a candidate public Cell Painting profile return toward a measured reference phenotype?

First, we load a small public CPJUMP1 processed-profile slice from the Cell Painting Gallery. We fit the untreated/control reference cloud from replicate wells, preserving the mean, variance, source plate and well records, and a file hash.

Next, we choose a shifted ORF perturbation: ALK on plate BR00117006. The reference-state model labels it CONTINUOUS with a covariance-aware distance of 3.483.

Then we rank compound profiles with the score R = 1 - D(candidate, reference) / D(perturbation, reference). The current top morphology candidate is TG-02, annotated to target CDK9, with restoration score 0.318. The best gene-linked benchmark row in the ranking is PF-06463922 to ALK with score -0.048.

Finally, we show the evidence chain: compound to target to pathway field, plus an FCO-style receipt containing the dataset, plate and well records, preprocessing recipe, hashes, calculation version, and result. If the score is changed after the fact, verification fails.

This is phenotypic restoration evidence from public morphology profiles. It is not a therapeutic, clinical, diagnostic, or measured-rescue claim.
