import math
import matplotlib.pyplot as plt


def getMaxDissimilarityForRevision(t):
    lamb = 0.001
    return (2**(-(t/(math.log(2)/lamb))))

plt.figure(figsize=(12, 8))
max_t = 2000

dmaxes = []
for t in range(1,max_t):
    dmax=getMaxDissimilarityForRevision(t)
    dmaxes.append(dmax)
    print(t, ":", dmax)

# plt.axhline(y=dmin, color="r")
plt.plot(range(1,max_t), dmaxes)
plt.show()


import numpy as np
import skfuzzy as fuzz

def computeAreaSKFuzzyMF(x, mfx):
    sum_area = 0.0
    # If the membership function is a singleton fuzzy set:
    if len(x) == 1:
        return (x[0] * mfx[0]
                / np.fmax(mfx[0], np.finfo(float).eps).astype(float))

    # else return the sum of moment*area/sum of area
    for i in range(1, len(x)):
        x1 = x[i - 1]
        x2 = x[i]
        y1 = mfx[i - 1]
        y2 = mfx[i]

        # if y1 == y2 == 0.0 or x1==x2: --> rectangle of zero height or width
        if not (y1 == y2 == 0.0 or x1 == x2):
            if y1 == y2:  # rectangle
                area = (x2 - x1) * y1
            elif y1 == 0.0 and y2 != 0.0:  # triangle, height y2
                area = 0.5 * (x2 - x1) * y2
            elif y2 == 0.0 and y1 != 0.0:  # triangle, height y1
                area = 0.5 * (x2 - x1) * y1
            else:
                area = 0.5 * (x2 - x1) * (y1 + y2)
            sum_area += area
    return sum_area


def getDissimilarity(umf1, mf1, umf2, mf2):
    """
    (Dubois and Prade [7 in the link below])
    https://pdf.sciencedirectassets.com/271876/1-s2.0-S0888613X00X00576/1-s2.0-0888613X87900156/main.pdf?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJ7%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJGMEQCICkkQjrKUh3KvT2RvPYJqTcFtAeh9BBGEPRa18L17hq%2BAiBM093i3SMgz3KAVZ6EaKOLAlqBSFa50r5ubjlyxaizxSrMBAhHEAUaDDA1OTAwMzU0Njg2NSIM9OOl9AwXQ3kVky3wKqkEYPGAQkGcGiMypnDcyCSoYPwUyaWMI5extaJYudFeB0v1oarA0K86bimnV%2FL4dvoL%2B%2FY7LVirsC0dGYNPec58ZoLSo36Rh9JzrYVSPGseXubNocU6CNgYhREw77PZmC0wQ9MQsfz11P6%2Bsm%2Fi%2BxLLFU6Rth6A3W0QM24Z38q789UKPNDmSkUYiO8BdHdaepljTUH3z2FXwLq7aalavFrNbXrR25As9JYAToHwwBQHnD1bGRFEINDVgrOS5iJE6xnCG4V9o3xramdW8c3C1f3caVN%2FOq1qsaKAlViRJ3Lb8vAwMKpDawZ3KX6GlB3GYr9yvDyBTL%2BcS5Hl5ih5tLNHZ3shxsvph0En8e2jDskHTXFhScpFPl%2FgaXdzM6cdd5DIKO2kVdPbHw%2Fq811lqXKghggfiK8VhQzo7QdR5U7%2BmRb6E2ksF5J7%2FRZq5z9baqO6W1sEscKx2uI55JIlriXOAVwjtt4xKhdFCT54Gld9mnSsT4lJwNvaQLO33srLu9%2FN35KZN%2Bhv1kGGhj3D9oIHtlQ4uZx%2FC8p2jOelQngbYKqOEd4kb421JKxogBfsDObPpb9jmDkWLY7of1FqIaQqfI0SeyhQuiCGRH43%2Fuwv%2BSz7BfIZIiWxncFBcew6tQ3%2F%2BqdFaZZVa%2FpJIs2upl62FgrC8LJUfGtSmaboZ3wNIflU4%2B0Gi4tS4sj4Fw9Xro%2B9GSei7KfTeRFDuG%2Fhk1hS2YwtBvyJk8wMxTCt5KGZBjqqATil3V9FhWQUoI5NpN69L70aMKUeOrOvL0dce8IrQT4polzk3TQVp6409plf1JTKAQ9mpyEhJM0b8XO3ZUkN%2B8woDrKdgHmnOccVm8ea9HeETOQqJpuBlAw8zdEDIJJc3mLgqajWI%2BSxafzx8ieOxVfy0IdAFf6OVD89YhYZEtInAGdJi%2FgYCd3CzOtcj%2FmMNIR6mIoyVAZ%2Ffkd2gZWY3YzO21fG2ij5F0mD&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20220919T144815Z&X-Amz-SignedHeaders=host&X-Amz-Expires=299&X-Amz-Credential=ASIAQ3PHCVTY2ZJ6LDSU%2F20220919%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=bf90aad1c2fc076122b616badefc9e00d15609501d1855abaaf05e4235cd1e44&hash=5bef54f94a5b21afbfb1b1400a92d7462a2e91c5d8e4a245cd9d4f35dbc34a8d&host=68042c943591013ac2b2430a89b270f6af2c76d8dfd086a07176afe7c76c2c61&pii=0888613X87900156&tid=spdf-ad01d91c-b587-4fe6-943d-4cbd1d7b6158&sid=187edd252b20f546de4942e0daecf6a64e58gxrqb&type=client&ua=5854015d5604545a07&rr=74d31f08eda50b43
    :param umf1:
    :param mf1:
    :param umf2:
    :param mf2:
    :return:
    """
    univ_int, inters = fuzz.fuzzy_and(umf1, mf1, umf2, mf2)
    univ_union, union = fuzz.fuzzy_or(umf1, mf1, umf2, mf2)
    aint = computeAreaSKFuzzyMF(univ_int, inters)
    aunion = computeAreaSKFuzzyMF(univ_union, union)
    return 1 - (aint / aunion)

umfs = np.arange(0, 100.000001, 0.05)
mf1 = fuzz.trapmf(umfs, [5,10,20,30])
mf2 = fuzz.trapmf(umfs, [4,45,45,80])

print(getDissimilarity(umfs, mf1, umfs, mf2))
for t in range(1, 2000):
    print(t, ":", getDissimilarity(umfs, mf1, umfs, mf2), getMaxDissimilarityForRevision(t),  getDissimilarity(umfs, mf1, umfs, mf2)<getMaxDissimilarityForRevision(t))
    print(t, ":", getDissimilarity(umfs, mf2, umfs, mf1), getMaxDissimilarityForRevision(t),  getDissimilarity(umfs, mf2, umfs, mf1)<getMaxDissimilarityForRevision(t))