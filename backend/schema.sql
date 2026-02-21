create table if not exists sync_state (
  id text primary key,
  cursor_updated_at timestamptz
);

create table if not exists prs (
  id bigint primary key,
  number int not null,
  author text,
  title text,
  state text,
  merged boolean not null,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  merged_at timestamptz,
  additions int not null,
  deletions int not null,
  changed_files int not null
);

create table if not exists reviews (
  id bigint primary key,
  pr_id bigint not null references prs(id) on delete cascade,
  reviewer text,
  state text,
  submitted_at timestamptz
);

create index if not exists idx_prs_updated_at on prs(updated_at);
create index if not exists idx_reviews_submitted on reviews(submitted_at);

insert into sync_state (id, cursor_updated_at)
values ('default', null)
on conflict (id) do nothing;
