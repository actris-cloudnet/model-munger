import numpy as np
from numpy import ma

from model_munger.metadata import ATTRIBUTES
from model_munger.model import Model


def merge_models(models: list[Model]) -> Model:
    times = []
    ftimes = []
    mindices = []
    tindices = []
    for i, model in enumerate(models):
        time = model.data["time"]
        ftime = model.data["forecast_time"]
        times.append(time)
        ftimes.append(ftime)
        mindices.append(np.full_like(time, i))
        tindices.append(np.arange(len(time)))
    time = np.concatenate(times)
    ftime = np.concatenate(ftimes)
    mindex = np.concatenate(mindices)
    tindex = np.concatenate(tindices)

    # Sort by forecast time.
    findex = np.argsort(ftime)
    time = time[findex]
    ftime = ftime[findex]
    mindex = mindex[findex]
    tindex = tindex[findex]

    # Sort and find unique times while keeping the smallest forecast time.
    utime, uindex = np.unique(time, return_index=True)
    mindex = mindex[uindex]
    tindex = tindex[uindex]

    # Initialize merged model with common scalar and 1D data.
    data = {
        key: values
        for key, values in models[0].data.items()
        if key != "time" and "time" not in ATTRIBUTES[key].dimensions
    }

    # Combine 2D data.
    for key in models[0].data:
        if key in data:
            continue
        values = []
        for i, t in zip(mindex, tindex, strict=True):
            if key in models[i].data:
                values.append(models[i].data[key][t : t + 1])
            else:
                shape = (1,) + models[0].data[key].shape[1:]
                values.append(ma.masked_all(shape))
        data[key] = ma.concatenate(values)

    used_models = [models[i] for i in np.unique(mindex)]
    return Model(
        models[0].type,
        models[0].location,
        data,
        sources=models[0].sources,
        comments=models[0].comments,
        history=[line for m in used_models for line in m.history],
    )
