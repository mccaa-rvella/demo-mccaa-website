import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../api/client';

interface Sector {
  id: number;
  name: string;
  slug: string;
  showcase: boolean;
  visit_count: number;
  article_id: number | null;
  consumer_article_id: number | null;
  has_business: boolean;
  has_consumer: boolean;
}

export function useTopSectors() {
  return useQuery<Sector[]>({
    queryKey: ['sectors', 'top'],
    queryFn: () => apiFetch('/sectors/top'),
  });
}

export function useAllSectors() {
  return useQuery<Sector[]>({
    queryKey: ['sectors', 'all'],
    queryFn: () => apiFetch('/sectors'),
  });
}
