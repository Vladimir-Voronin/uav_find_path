import math


def grad_to_rad(grad):
    return grad / 360 * math.pi * 2


def cos_by_grad(grad):
    return math.cos(grad_to_rad(grad))


def sin_by_grad(grad):
    return math.sin(grad_to_rad(grad))
