with C as (
SELECT 
  video_id
  ,min(timestampUsec) as min_time
  ,max(timestampUsec) as max_time
FROM `{project_id}.livechatlog.chatlog`
group by
  video_id
), CT as (
  select
    video_id
    ,time(timestamp_micros(cast(max_time - min_time as INT64))) as chatlog_time
  from C
)
SELECT 
  name
  ,channel_id
  ,title
  ,V.video_id
  ,time_duration
  ,chatlog_time
  ,time_diff(time_duration, chatlog_time, second) as diff_time
FROM `{project_id}.Vtuber.v_videos` V
left outer join CT
  on V.video_id = CT.video_id 
where
  time_diff(time_duration, chatlog_time, second) > 600
;
