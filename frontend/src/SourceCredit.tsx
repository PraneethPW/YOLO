import type {Source} from './types';

export default function SourceCredit({source}:{source:Source}){
 if(!source.credit)return null;
 return <p className="source-credit">{source.reference_url?.startsWith('https://')?<a href={source.reference_url} target="_blank" rel="noopener noreferrer">{source.credit}</a>:source.credit}</p>;
}
