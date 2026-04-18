import json
from helen_os_mvp.tools.memory_replay import replay, canon


def test_replay_determinism():
    events = [
        {"schema_version":"MEMORY_V1","event_id":"a1","t":"2026-02-25T10:00:00Z","type":"memory_observation","actor":"assistant","key":"user.preference.tone","value":"rigorous","status":"OBSERVED","source":{"turn_id":1,"message_id":None,"span":None}},
        {"schema_version":"MEMORY_V1","event_id":"a2","t":"2026-02-25T10:00:01Z","type":"memory_confirmation_request","actor":"assistant","key":"user.preference.tone","value":None,"status":"DISPUTED","request":{"request_id":"r1","question":"Confirm tone?","options":["confirm_new","confirm_old","keep_both"]}},
        {"schema_version":"MEMORY_V1","event_id":"a3","t":"2026-02-25T10:00:02Z","type":"memory_confirmation_response","actor":"user","key":"user.preference.tone","value":None,"status":"CONFIRMED","response":{"request_id":"r1","choice":"confirm_new"}},
        {"schema_version":"MEMORY_V1","event_id":"a4","t":"2026-02-25T10:00:03Z","type":"memory_resolution","actor":"system","key":"user.preference.tone","value":None,"status":"CONFIRMED","resolution":{"request_id":"r1","kept":["a1"],"status_updates":[{"event_id":"a1","status":"CONFIRMED"}]}}
    ]
    kv1, pending1, h1 = replay(events)
    kv2, pending2, h2 = replay(events)
    assert canon(kv1) == canon(kv2)
    assert canon({k:v.__dict__ for k,v in pending1.items()}) == canon({k:v.__dict__ for k,v in pending2.items()})
    assert h1 == h2
