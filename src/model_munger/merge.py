import numpy as np
from numpy import ma
from model_munger.metadata import ATTRIBUTES
from model_munger.model import Model


def merge_models(models: list[Model]) -> Model:
    times = []
    index = []
    tinde = []
    ordered_models = sorted(
        enumerate(models), key=lambda item: item[1].data["time"][0], reverse=True
    )
    for i, model in ordered_models:
        time = model.data["time"]
        times.append(time)
        index.append(np.full_like(time, i))
        tinde.append(np.arange(len(time)))
    time = np.concatenate(times)
    index = np.concatenate(index)
    tinde = np.concatenate(tinde)
    utime, uindex = np.unique(time, return_index=True)
    data = {
        key: values
        for key, values in models[0].data.items()
        if key != "time" and "time" not in ATTRIBUTES[key].dimensions
    }
    for key in models[0].data.keys():
        if key in data:
            continue
        values = []
        for i, t in zip(index[uindex], tinde[uindex]):
            values.append(models[i].data[key][t : t + 1])
        data[key] = ma.concatenate(values)
    return Model(
        models[0].type,
        models[0].location,
        data,
        history=[line for m in models for line in m.history],
    )
