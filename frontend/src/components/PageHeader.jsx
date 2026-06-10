import { Typography } from "antd";

export default function PageHeader({ title, description, action }) {
  return (
    <div className="page-header">
      <div>
        <Typography.Title level={3}>{title}</Typography.Title>
        {description ? (
          <Typography.Paragraph type="secondary">
            {description}
          </Typography.Paragraph>
        ) : null}
      </div>
      {action}
    </div>
  );
}
